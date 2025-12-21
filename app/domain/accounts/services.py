from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

from advanced_alchemy.service import (
    ModelDictT,
    SQLAlchemyAsyncRepositoryService,
    is_dict,
    is_dict_with_field,
    is_dict_without_field,
    schema_dump,
)
from advanced_alchemy.types import FileObject
from litestar.exceptions import NotAuthorizedException, PermissionDeniedException, ValidationException
from sqlalchemy.orm import undefer_group
from uuid_utils import uuid7

from app.db.models import EmailToken, Role, TokenType, User, UserOauthAccount, UserRole
from app.domain.accounts.repositories import (
    EmailTokenRepository,
    RoleRepository,
    UserOauthAccountRepository,
    UserRepository,
    UserRoleRepository,
)
from app.lib import crypt

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class MfaVerifyResult:
    """Result of MFA verification attempt."""

    user: User
    """The user being verified."""
    verified: bool
    """Whether the MFA code was valid."""
    mfa_disabled: bool = False
    """True if MFA was found to be disabled (user can proceed without verification)."""
    used_backup_code: bool = False
    """True if a backup code was used instead of TOTP."""
    remaining_backup_codes: int = 0
    """Number of backup codes remaining after this verification."""


class UserService(SQLAlchemyAsyncRepositoryService[User, UserRepository]):
    """Handles database operations for users."""

    repository_type = UserRepository
    default_role = "Application Access"

    async def to_model_on_create(self, data: ModelDictT[User]) -> ModelDictT[User]:
        """Transform data before creating a user.

        Returns:
            Transformed user data with hashed password and role.
        """
        data = schema_dump(data)
        data = await self._populate_with_hashed_password(data)
        return await self._populate_with_role(data)

    async def to_model_on_update(self, data: ModelDictT[User]) -> ModelDictT[User]:
        """Transform data before updating a user.

        Returns:
            Transformed user data with hashed password and role if provided.
        """
        data = schema_dump(data)
        data = await self._populate_with_hashed_password(data)
        return await self._populate_with_role(data)

    async def _populate_with_hashed_password(self, data: ModelDictT[User]) -> ModelDictT[User]:
        """Hash password if provided.

        Returns:
            User data with password replaced by hashed_password.
        """
        if is_dict(data) and (password := data.pop("password", None)) is not None:
            data["hashed_password"] = await crypt.get_password_hash(password)
        return data

    async def _populate_with_role(self, data: ModelDictT[User]) -> ModelDictT[User]:
        """Assign role if role_id provided.

        Returns:
            User data with role assignment if role_id was provided.
        """
        if is_dict(data) and (role_id := data.pop("role_id", None)) is not None:
            data = await super().to_model(data)
            data.roles.append(UserRole(role_id=role_id, assigned_at=datetime.now(UTC)))
        return data

    async def authenticate(self, username: str, password: bytes | str) -> User:
        """Authenticate a user.

        Args:
            username: The user's email address.
            password: The user's password.

        Raises:
            NotAuthorizedException: Raised when the user doesn't exist, isn't verified, or is not active.

        Returns:
            User: The user object with credentials loaded.
        """
        db_obj = await self.get_one_or_none(email=username, load=[undefer_group("security_sensitive")])
        if db_obj is None:
            msg = "User not found or password invalid"
            raise NotAuthorizedException(detail=msg)
        if db_obj.hashed_password is None:
            msg = "User not found or password invalid."
            raise NotAuthorizedException(detail=msg)
        if not await crypt.verify_password(password, db_obj.hashed_password):
            msg = "User not found or password invalid"
            raise NotAuthorizedException(detail=msg)
        if not db_obj.is_active:
            msg = "User account is inactive"
            raise NotAuthorizedException(detail=msg)
        return db_obj

    async def update_password(self, data: dict[str, Any], db_obj: User) -> None:
        """Update stored user password with current password verification.

        This is used when the user knows their current password.

        Args:
            data: Dict containing current_password and new_password.
            db_obj: User database object (credentials will be loaded if needed).

        Raises:
            PermissionDeniedException: If current password is invalid or user inactive.
        """
        # Re-fetch user with credentials since db_obj may have deferred columns
        user_with_creds = await self.get_one_or_none(id=db_obj.id, load=[undefer_group("security_sensitive")])
        if user_with_creds is None:
            msg = "User not found or password invalid."
            raise PermissionDeniedException(detail=msg)
        if user_with_creds.hashed_password is None:
            msg = "User not found or password invalid."
            raise PermissionDeniedException(detail=msg)
        if not await crypt.verify_password(data["current_password"], user_with_creds.hashed_password):
            msg = "User not found or password invalid."
            raise PermissionDeniedException(detail=msg)
        if not user_with_creds.is_active:
            msg = "User account is not active"
            raise PermissionDeniedException(detail=msg)
        user_with_creds.hashed_password = await crypt.get_password_hash(data["new_password"])
        await self.repository.update(user_with_creds)

    async def reset_password(self, new_password: str, db_obj: User) -> None:
        """Reset user password without current password verification.

        Used for password reset flows where user has verified identity via email token.

        Args:
            new_password: The new password to set.
            db_obj: User database object.

        Raises:
            PermissionDeniedException: If user account is inactive.
        """
        if not db_obj.is_active:
            msg = "User account is not active"
            raise PermissionDeniedException(detail=msg)
        db_obj.hashed_password = await crypt.get_password_hash(new_password)
        await self.repository.update(db_obj)

    async def verify_mfa(
        self, email: str, code: str | None = None, recovery_code: str | None = None,
    ) -> MfaVerifyResult:
        """Verify MFA code or recovery code for a user.

        Loads user credentials, verifies TOTP or backup code, and consumes
        the backup code if used.

        Args:
            email: User's email address.
            code: TOTP code from authenticator app.
            recovery_code: Backup recovery code.

        Raises:
            PermissionDeniedException: If user not found.

        Returns:
            MfaVerifyResult with verification status and details.
        """
        user = await self.get_one_or_none(email=email, load=[undefer_group("security_sensitive")])
        if not user:
            msg = "User not found"
            raise PermissionDeniedException(detail=msg)

        # Check if MFA is actually enabled
        if not user.totp_secret or not user.is_two_factor_enabled:
            return MfaVerifyResult(user=user, verified=True, mfa_disabled=True)

        # Try TOTP code first
        if code and await crypt.verify_totp_code(user.totp_secret, code):
            return MfaVerifyResult(user=user, verified=True)

        # Try recovery code
        if recovery_code and user.backup_codes:
            code_index = await crypt.verify_backup_code(recovery_code, user.backup_codes)
            if code_index is not None:
                # Consume the backup code
                updated_codes = user.backup_codes.copy()
                updated_codes.pop(code_index)
                await self.update(item_id=user.id, data={"backup_codes": updated_codes or None})
                return MfaVerifyResult(
                    user=user, verified=True, used_backup_code=True, remaining_backup_codes=len(updated_codes),
                )

        return MfaVerifyResult(user=user, verified=False)

    @staticmethod
    async def has_role_id(db_obj: User, role_id: UUID) -> bool:
        """Check if user has specified role ID.

        Returns:
            True if user has the role, False otherwise.
        """
        return any(assigned_role.role_id for assigned_role in db_obj.roles if assigned_role.role_id == role_id)

    @staticmethod
    async def has_role(db_obj: User, role_name: str) -> bool:
        """Check if user has specified role name.

        Returns:
            True if user has the role, False otherwise.
        """
        return any(assigned_role.role_id for assigned_role in db_obj.roles if assigned_role.role_name == role_name)

    @staticmethod
    def is_superuser(user: User) -> bool:
        """Check if user is a superuser.

        Returns:
            True if user is a superuser, False otherwise.
        """
        return bool(
            user.is_superuser
            or any(assigned_role.role.name for assigned_role in user.roles if assigned_role.role.name == "Superuser"),
        )

    # Avatar upload settings
    ALLOWED_AVATAR_TYPES: set[str] = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    MAX_AVATAR_SIZE: int = 5 * 1024 * 1024  # 5MB

    async def upload_avatar(self, user: User, content: bytes, content_type: str, original_filename: str) -> User:
        """Upload and save user avatar.

        Args:
            user: User to update.
            content: File content bytes.
            content_type: MIME type of the file.
            original_filename: Original filename.

        Returns:
            Updated user with new avatar.

        Raises:
            ValidationException: If file type or size is invalid.
        """
        if content_type not in self.ALLOWED_AVATAR_TYPES:
            msg = f"Invalid file type. Allowed: {', '.join(self.ALLOWED_AVATAR_TYPES)}"
            raise ValidationException(detail=msg)

        if len(content) > self.MAX_AVATAR_SIZE:
            msg = f"File too large. Maximum size: {self.MAX_AVATAR_SIZE // (1024 * 1024)}MB"
            raise ValidationException(detail=msg)

        # Advanced Alchemy automatically saves the new file and deletes the old one on commit
        ext = Path(original_filename).suffix.lower() or self._get_extension(content_type)
        unique_filename = f"avatars/{user.id}/{uuid7()}{ext}"

        user.avatar = FileObject(
            backend="avatars", filename=unique_filename, content_type=content_type, content=content,
        )
        return await self.update(user, auto_commit=True)

    async def delete_avatar(self, user: User) -> User:
        """Delete user avatar and revert to Gravatar.

        Args:
            user: User to update.

        Returns:
            Updated user without avatar.
        """
        if user.avatar is not None:
            user.avatar = None
            return await self.update(user, auto_commit=True)
        return user

    @staticmethod
    def _get_extension(content_type: str) -> str:
        """Get file extension from content type.

        Args:
            content_type: MIME type.

        Returns:
            File extension including dot.
        """
        extensions = {"image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif", "image/webp": ".webp"}
        return extensions.get(content_type, ".jpg")


class RoleService(SQLAlchemyAsyncRepositoryService[Role, RoleRepository]):
    """Handles database operations for roles."""

    repository_type = RoleRepository
    match_fields = ["name"]

    async def to_model_on_create(self, data: ModelDictT[Role]) -> ModelDictT[Role]:
        """Auto-generate slug on create if not provided.

        Returns:
            Role data with auto-generated slug if not provided.
        """
        data = schema_dump(data)
        if is_dict_without_field(data, "slug"):
            data["slug"] = await self.repository.get_available_slug(data["name"])
        return data

    async def to_model_on_update(self, data: ModelDictT[Role]) -> ModelDictT[Role]:
        """Auto-generate slug on update if name changed but no slug provided.

        Returns:
            Role data with auto-generated slug if name changed without slug.
        """
        data = schema_dump(data)
        if is_dict_without_field(data, "slug") and is_dict_with_field(data, "name"):
            data["slug"] = await self.repository.get_available_slug(data["name"])
        return data


class UserRoleService(SQLAlchemyAsyncRepositoryService[UserRole, UserRoleRepository]):
    """Handles database operations for user roles."""

    repository_type = UserRoleRepository


class UserOAuthAccountService(SQLAlchemyAsyncRepositoryService[UserOauthAccount, UserOauthAccountRepository]):
    """Handles database operations for user OAuth accounts."""

    repository_type = UserOauthAccountRepository


class EmailTokenService(SQLAlchemyAsyncRepositoryService[EmailToken, EmailTokenRepository]):
    """Service for managing email tokens.

    Handles creation, validation, and consumption of secure tokens
    for email verification, password reset, and similar flows.

    Tokens are hashed (SHA-256) before storage - plain tokens are
    only returned once during creation.
    """

    repository_type = EmailTokenRepository

    @staticmethod
    def _hash_token(token: str) -> str:
        """Hash a token using SHA-256.

        Args:
            token: Plain text token to hash.

        Returns:
            SHA-256 hex digest of the token.
        """
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def _generate_token() -> str:
        """Generate a secure random token.

        Returns:
            URL-safe base64 encoded random token.
        """
        return secrets.token_urlsafe(32)

    async def to_model_on_create(self, data: ModelDictT[EmailToken]) -> ModelDictT[EmailToken]:
        """Auto-hash token if plain token is provided.

        Returns:
            Token data with hashed token.
        """
        data = schema_dump(data)
        if is_dict_with_field(data, "token") and is_dict_without_field(data, "token_hash"):
            data["token_hash"] = self._hash_token(data.pop("token"))
        return data

    async def create_token(
        self,
        email: str,
        token_type: TokenType,
        expires_delta: timedelta,
        user_id: UUID | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata: dict | None = None,
    ) -> tuple[EmailToken, str]:
        """Create a new email token.

        Returns:
            Tuple of (database record, plain token). Plain token should be sent to user via email.
        """
        token = self._generate_token()
        return await self.create(
            {
                "email": email,
                "token_type": token_type,
                "token": token,  # to_model_on_create hashes this
                "expires_at": datetime.now(UTC) + expires_delta,
                "user_id": user_id,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "metadata_": metadata or {},
            },
            auto_commit=True,
        ), token

    async def validate_token(
        self, plain_token: str, token_type: TokenType, email: str | None = None,
    ) -> EmailToken | None:
        """Validate a token without consuming it.

        Returns:
            EmailToken record if valid, None otherwise.
        """
        token = await self.get_one_or_none(token_hash=self._hash_token(plain_token), token_type=token_type)
        if token is None or not token.is_valid or (email and token.email != email):
            return None
        return token

    async def consume_token(
        self, plain_token: str, token_type: TokenType, email: str | None = None,
    ) -> EmailToken | None:
        """Validate and consume a token. Token cannot be used again after consumption.

        Returns:
            EmailToken record if valid and consumed, None otherwise.
        """
        if (token := await self.validate_token(plain_token, token_type, email)) is None:
            return None
        token.mark_used()
        await self.update(token, auto_commit=True)
        return token

    async def invalidate_existing_tokens(self, email: str, token_type: TokenType) -> int:
        """Invalidate all existing valid tokens of a type for an email.

        Returns:
            Number of tokens invalidated.
        """
        tokens = [t for t in await self.list(email=email, token_type=token_type, used_at=None) if t.is_valid]
        for token in tokens:
            token.mark_used()
            await self.update(token, auto_commit=False)
        if tokens:
            await self.repository.session.commit()
        return len(tokens)


async def provide_email_token_service(db_session: AsyncSession) -> EmailTokenService:
    """Provide EmailTokenService instance.

    Args:
        db_session: Database session.

    Returns:
        Configured EmailTokenService instance.
    """
    return EmailTokenService(session=db_session)

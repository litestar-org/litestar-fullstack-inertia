from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any
from uuid import UUID  # noqa: TC003

from advanced_alchemy.service import (
    ModelDictT,
    SQLAlchemyAsyncRepositoryService,
    is_dict,
    is_dict_with_field,
    is_dict_without_field,
    schema_dump,
)
from litestar.exceptions import NotAuthorizedException, PermissionDeniedException

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
    from sqlalchemy.ext.asyncio import AsyncSession


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
            User: The user object
        """
        db_obj = await self.get_one_or_none(email=username)
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
            db_obj: User database object.

        Raises:
            PermissionDeniedException: If current password is invalid or user inactive.
        """
        if db_obj.hashed_password is None:
            msg = "User not found or password invalid."
            raise PermissionDeniedException(detail=msg)
        if not await crypt.verify_password(data["current_password"], db_obj.hashed_password):
            msg = "User not found or password invalid."
            raise PermissionDeniedException(detail=msg)
        if not db_obj.is_active:
            msg = "User account is not active"
            raise PermissionDeniedException(detail=msg)
        db_obj.hashed_password = await crypt.get_password_hash(data["new_password"])
        await self.repository.update(db_obj)

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
            or any(assigned_role.role.name for assigned_role in user.roles if assigned_role.role.name in {"Superuser"}),
        )


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
                "token_hash": self._hash_token(token),
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

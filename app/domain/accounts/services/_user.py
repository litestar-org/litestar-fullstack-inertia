from __future__ import annotations

import base64
import secrets
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pyotp
import qrcode  # type: ignore[import-untyped]
from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import ModelDictT, SQLAlchemyAsyncRepositoryService, is_dict, schema_dump
from advanced_alchemy.types import FileObject
from litestar.exceptions import NotAuthorizedException, PermissionDeniedException, ValidationException
from sqlalchemy.orm import undefer_group
from uuid_utils import uuid7

from app.db.models import User, UserRole
from app.lib import crypt

if TYPE_CHECKING:
    from uuid import UUID


class MfaVerifyResult:
    """Result of MFA verification attempt."""

    __slots__ = ("mfa_disabled", "remaining_backup_codes", "used_backup_code", "user", "verified")

    def __init__(
        self,
        user: User,
        verified: bool,
        mfa_disabled: bool = False,
        used_backup_code: bool = False,
        remaining_backup_codes: int = 0,
    ) -> None:
        self.user = user
        self.verified = verified
        self.mfa_disabled = mfa_disabled
        self.used_backup_code = used_backup_code
        self.remaining_backup_codes = remaining_backup_codes


async def generate_backup_codes(count: int = 8) -> tuple[list[str], list[str]]:
    """Generate backup codes and their hashes.

    Returns:
        Tuple of (plain_codes, hashed_codes).
    """
    plain_codes = [secrets.token_hex(4).upper() for _ in range(count)]
    hashed_codes: list[str] = [await crypt.hash_backup_code(code) for code in plain_codes]
    return plain_codes, hashed_codes


def generate_qr_code(secret: str, email: str, issuer: str = "Litestar Fullstack") -> str:
    """Generate a QR code for TOTP setup.

    Returns:
        Base64 encoded PNG image.
    """
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(name=email, issuer_name=issuer)

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, "PNG")
    buffer.seek(0)

    return base64.b64encode(buffer.getvalue()).decode("utf-8")


class UserService(SQLAlchemyAsyncRepositoryService[User]):
    """Handles database operations for users."""

    class Repo(SQLAlchemyAsyncRepository[User]):
        """User SQLAlchemy Repository."""

        model_type = User

    repository_type = Repo
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
        self,
        email: str,
        code: str | None = None,
        recovery_code: str | None = None,
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
                    user=user,
                    verified=True,
                    used_backup_code=True,
                    remaining_backup_codes=len(updated_codes),
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
            backend="avatars",
            filename=unique_filename,
            content_type=content_type,
            content=content,
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

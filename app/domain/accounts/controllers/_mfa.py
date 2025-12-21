"""MFA (Multi-Factor Authentication) management controller."""

from __future__ import annotations

from datetime import UTC, datetime

import pyotp
from litestar import Controller, Request, delete, post
from litestar.di import Provide
from litestar.exceptions import PermissionDeniedException, ValidationException
from litestar_vite.inertia import InertiaRedirect, flash
from sqlalchemy.orm import undefer_group

from app.domain.accounts.dependencies import provide_users_service
from app.domain.accounts.schemas import MfaBackupCodes, MfaConfirm, MfaDisable, MfaSetup
from app.domain.accounts.services import UserService, generate_backup_codes, generate_qr_code
from app.lib import crypt

__all__ = ("MfaController",)

# Exception messages
_MSG_AUTH_REQUIRED = "Authentication required"
_MSG_USER_NOT_FOUND = "User not found"
_MSG_MFA_ALREADY_ENABLED = "MFA is already enabled"
_MSG_MFA_ALREADY_CONFIRMED = "MFA is already confirmed"
_MSG_MFA_NOT_INITIATED = "MFA setup not initiated. Please enable MFA first."
_MSG_MFA_NOT_ENABLED = "MFA is not enabled"
_MSG_INVALID_CODE = "Invalid verification code"
_MSG_INVALID_CREDENTIALS = "Invalid password"


class MfaController(Controller):
    """MFA (Multi-Factor Authentication) management."""

    path = "/mfa"
    include_in_schema = False
    dependencies = {"users_service": Provide(provide_users_service)}
    signature_namespace = {"UserService": UserService}
    cache = False

    @post(path="/enable", name="mfa.enable")
    async def enable_mfa(self, request: Request, users_service: UserService) -> MfaSetup:
        """Generate TOTP secret and QR code for MFA setup.

        Raises:
            PermissionDeniedException: If user is not authenticated.
            ValidationException: If MFA is already enabled.

        Returns:
            MfaSetup with secret and QR code.
        """
        user_id = request.session.get("user_id")
        if not user_id:
            raise PermissionDeniedException(_MSG_AUTH_REQUIRED)

        user = await users_service.get_one_or_none(email=user_id)
        if not user:
            raise PermissionDeniedException(_MSG_USER_NOT_FOUND)

        if user.is_two_factor_enabled:
            raise ValidationException(_MSG_MFA_ALREADY_ENABLED)

        # Generate new TOTP secret
        secret = pyotp.random_base32()
        qr_code = generate_qr_code(secret, user.email)

        # Store secret temporarily (not confirmed yet)
        await users_service.update(item_id=user.id, data={"totp_secret": secret, "is_two_factor_enabled": False})

        return MfaSetup(secret=secret, qr_code=qr_code)

    @post(path="/confirm", name="mfa.confirm")
    async def confirm_mfa(self, request: Request, users_service: UserService, data: MfaConfirm) -> MfaBackupCodes:
        """Confirm MFA setup with a valid TOTP code.

        Raises:
            PermissionDeniedException: If user is not authenticated.
            ValidationException: If MFA not initiated, already confirmed, or code is invalid.

        Returns:
            Backup codes for account recovery.
        """
        user_id = request.session.get("user_id")
        if not user_id:
            raise PermissionDeniedException(_MSG_AUTH_REQUIRED)

        # Need credentials to access totp_secret
        user = await users_service.get_one_or_none(email=user_id, load=[undefer_group("security_sensitive")])
        if not user:
            raise PermissionDeniedException(_MSG_USER_NOT_FOUND)

        if not user.totp_secret:
            raise ValidationException(_MSG_MFA_NOT_INITIATED)

        if user.is_two_factor_enabled:
            raise ValidationException(_MSG_MFA_ALREADY_CONFIRMED)

        # Verify the TOTP code
        if not await crypt.verify_totp_code(user.totp_secret, data.code):
            raise ValidationException(_MSG_INVALID_CODE)

        # Generate backup codes
        plain_codes, hashed_codes = await generate_backup_codes()

        # Enable MFA
        await users_service.update(
            item_id=user.id,
            data={
                "is_two_factor_enabled": True,
                "two_factor_confirmed_at": datetime.now(UTC),
                "backup_codes": hashed_codes,
            },
        )

        flash(request, "MFA has been enabled.", category="success")
        return MfaBackupCodes(codes=plain_codes)

    @delete(path="/disable", name="mfa.disable", status_code=303)
    async def disable_mfa(self, request: Request, users_service: UserService, data: MfaDisable) -> InertiaRedirect:
        """Disable MFA with password confirmation.

        Raises:
            PermissionDeniedException: If user is not authenticated.
            ValidationException: If MFA not enabled or password is invalid.

        Returns:
            Redirect to profile page.
        """
        user_id = request.session.get("user_id")
        if not user_id:
            raise PermissionDeniedException(_MSG_AUTH_REQUIRED)

        # Need credentials to verify password
        user = await users_service.get_one_or_none(email=user_id, load=[undefer_group("security_sensitive")])
        if not user:
            raise PermissionDeniedException(_MSG_USER_NOT_FOUND)

        if not user.is_two_factor_enabled:
            raise ValidationException(_MSG_MFA_NOT_ENABLED)

        # Verify password
        if not user.hashed_password or not await crypt.verify_password(data.password, user.hashed_password):
            raise ValidationException(_MSG_INVALID_CREDENTIALS)

        # Disable MFA
        await users_service.update(
            item_id=user.id,
            data={
                "totp_secret": None,
                "is_two_factor_enabled": False,
                "two_factor_confirmed_at": None,
                "backup_codes": None,
            },
        )

        flash(request, "MFA has been disabled.", category="info")
        return InertiaRedirect(request, request.url_for("profile.edit"))

    @post(path="/regenerate-codes", name="mfa.regenerate-codes")
    async def regenerate_backup_codes(self, request: Request, users_service: UserService) -> MfaBackupCodes:
        """Regenerate backup codes for MFA recovery.

        Raises:
            PermissionDeniedException: If user is not authenticated.
            ValidationException: If MFA not enabled.

        Returns:
            New backup codes.
        """
        user_id = request.session.get("user_id")
        if not user_id:
            raise PermissionDeniedException(_MSG_AUTH_REQUIRED)

        user = await users_service.get_one_or_none(email=user_id)
        if not user:
            raise PermissionDeniedException(_MSG_USER_NOT_FOUND)

        if not user.is_two_factor_enabled:
            raise ValidationException(_MSG_MFA_NOT_ENABLED)

        # Generate new backup codes
        plain_codes, hashed_codes = await generate_backup_codes()

        await users_service.update(item_id=user.id, data={"backup_codes": hashed_codes})

        flash(request, "Backup codes have been regenerated.", category="success")
        return MfaBackupCodes(codes=plain_codes)

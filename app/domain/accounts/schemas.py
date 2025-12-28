from __future__ import annotations

from datetime import datetime  # noqa: TC003
from uuid import UUID  # noqa: TC003

import msgspec

from app.db.models.team_roles import TeamRoles
from app.lib.schema import CamelizedBaseStruct

__all__ = (
    "AccountLogin",
    "AccountRegister",
    "EmailSent",
    "ForgotPasswordRequest",
    "MfaBackupCodes",
    "MfaChallenge",
    "MfaConfirm",
    "MfaDisable",
    "MfaSetup",
    "PasswordReset",
    "PasswordResetToken",
    "PasswordUpdate",
    "PasswordVerify",
    "ProfileUpdate",
    "User",
    "UserCreate",
    "UserRole",
    "UserRoleAdd",
    "UserRoleRevoke",
    "UserTeam",
    "UserUpdate",
)


class UserTeam(CamelizedBaseStruct):
    """Holds team details for a user.

    This is nested in the User Model for 'team'
    """

    team_id: UUID
    team_name: str
    team_slug: str
    is_owner: bool = False
    role: TeamRoles = TeamRoles.MEMBER


class UserRole(CamelizedBaseStruct):
    """Holds role details for a user.

    This is nested in the User Model for 'roles'
    """

    role_id: UUID
    role_slug: str
    role_name: str
    assigned_at: datetime


class OauthAccount(CamelizedBaseStruct):
    """Holds linked OAuth details for a user.

    Note: Sensitive fields (access_token, refresh_token, expires_at) are
    intentionally excluded from this schema to prevent exposure to the frontend.
    """

    id: UUID
    oauth_name: str
    account_id: str
    account_email: str
    scopes: list[str] | None = None


class User(CamelizedBaseStruct):
    """User properties to use for a response."""

    id: UUID
    email: str
    name: str | None = None
    is_superuser: bool = False
    is_active: bool = False
    is_verified: bool = False
    has_password: bool = False
    is_two_factor_enabled: bool = False
    teams: list[UserTeam] = msgspec.field(default_factory=list)
    roles: list[UserRole] = msgspec.field(default_factory=list)
    oauth_accounts: list[OauthAccount] = msgspec.field(default_factory=list)
    avatar_url: str | None = None


class UserCreate(CamelizedBaseStruct):
    email: str
    password: str
    name: str | None = None
    is_superuser: bool = False
    is_active: bool = True
    is_verified: bool = False


class UserUpdate(CamelizedBaseStruct, omit_defaults=True):
    email: str | None | msgspec.UnsetType = msgspec.UNSET
    password: str | None | msgspec.UnsetType = msgspec.UNSET
    name: str | None | msgspec.UnsetType = msgspec.UNSET
    is_superuser: bool | None | msgspec.UnsetType = msgspec.UNSET
    is_active: bool | None | msgspec.UnsetType = msgspec.UNSET
    is_verified: bool | None | msgspec.UnsetType = msgspec.UNSET


class AccountLogin(CamelizedBaseStruct):
    username: str
    password: str


class PasswordUpdate(CamelizedBaseStruct):
    current_password: str
    new_password: str


class PasswordVerify(CamelizedBaseStruct):
    current_password: str


class ProfileUpdate(CamelizedBaseStruct, omit_defaults=True):
    name: str | None | msgspec.UnsetType = msgspec.UNSET


class AccountRegister(CamelizedBaseStruct):
    email: str
    password: str
    name: str | None = None


class UserRoleAdd(CamelizedBaseStruct):
    """User role add ."""

    user_name: str


class UserRoleRevoke(CamelizedBaseStruct):
    """User role revoke ."""

    user_name: str


class ForgotPasswordRequest(CamelizedBaseStruct):
    """Request to send a password reset email."""

    email: str


class PasswordReset(CamelizedBaseStruct):
    """Reset password with token."""

    token: str
    password: str


class EmailSent(CamelizedBaseStruct):
    """Confirmation that an email was sent."""

    email_sent: bool = True


class PasswordResetToken(CamelizedBaseStruct):
    """Token data for password reset form."""

    token: str
    email: str


class MfaSetup(CamelizedBaseStruct):
    """Response with QR code and secret for MFA setup."""

    secret: str
    qr_code: str  # Base64 encoded PNG


class MfaConfirm(CamelizedBaseStruct):
    """Request to confirm MFA setup with a TOTP code."""

    code: str


class MfaChallenge(CamelizedBaseStruct):
    """Request to verify MFA during login."""

    code: str | None = None
    recovery_code: str | None = None


class MfaDisable(CamelizedBaseStruct):
    """Request to disable MFA with password confirmation."""

    password: str


class MfaBackupCodes(CamelizedBaseStruct):
    """Response with backup codes for MFA recovery."""

    codes: list[str]


class PasswordConfirm(CamelizedBaseStruct):
    """Request to confirm password before sensitive actions."""

    password: str

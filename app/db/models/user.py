from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from advanced_alchemy.base import UUIDAuditBase
from advanced_alchemy.types import EncryptedString
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.lib.settings import get_settings

if TYPE_CHECKING:
    from .oauth_account import UserOauthAccount
    from .team_member import TeamMember
    from .user_role import UserRole

settings = get_settings()


class User(UUIDAuditBase):
    __tablename__ = "user_account"
    __table_args__ = {"comment": "User accounts for application access"}
    __pii_columns__ = {"name", "email", "avatar_url", "totp_secret"}

    email: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    name: Mapped[str | None] = mapped_column(nullable=True, default=None)
    hashed_password: Mapped[str | None] = mapped_column(
        String(length=255), nullable=True, default=None, deferred=True, deferred_group="security_sensitive"
    )
    avatar_url: Mapped[str | None] = mapped_column(String(length=500), nullable=True, default=None)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    verified_at: Mapped[date] = mapped_column(nullable=True, default=None)
    joined_at: Mapped[date] = mapped_column(default=datetime.now)

    # Multi-Factor Authentication (MFA/TOTP)
    totp_secret: Mapped[str | None] = mapped_column(
        EncryptedString(key=settings.app.SECRET_KEY),
        nullable=True,
        default=None,
        deferred=True,
        deferred_group="security_sensitive",
        comment="Encrypted TOTP secret key for MFA",
    )
    """Encrypted TOTP secret for generating time-based one-time passwords."""

    is_two_factor_enabled: Mapped[bool] = mapped_column(
        default=False, nullable=False, comment="Whether MFA is enabled for this user"
    )
    """Whether multi-factor authentication is currently active."""

    two_factor_confirmed_at: Mapped[datetime | None] = mapped_column(
        nullable=True, default=None, comment="When MFA was confirmed/enabled"
    )
    """Timestamp when MFA was successfully configured."""

    backup_codes: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
        default=None,
        deferred=True,
        deferred_group="security_sensitive",
        comment="Hashed backup codes for MFA recovery",
    )
    """JSON array of hashed backup codes for account recovery."""

    # -----------
    # ORM Relationships
    # ------------

    roles: Mapped[list[UserRole]] = relationship(
        back_populates="user", lazy="selectin", uselist=True, cascade="all, delete"
    )
    teams: Mapped[list[TeamMember]] = relationship(
        back_populates="user", lazy="selectin", uselist=True, cascade="all, delete", viewonly=True
    )
    oauth_accounts: Mapped[list[UserOauthAccount]] = relationship(
        back_populates="user", lazy="noload", cascade="all, delete", uselist=True
    )

    @hybrid_property
    def has_password(self) -> bool:
        return self.hashed_password is not None

    @hybrid_property
    def has_mfa(self) -> bool:
        """Check if user has MFA enabled.

        Note: This only checks is_two_factor_enabled to avoid loading deferred totp_secret.
        For full verification (including secret presence), use is_two_factor_enabled
        after loading credentials with undefer_group("security_sensitive").

        Returns:
            True if MFA is enabled, False otherwise.
        """
        return self.is_two_factor_enabled

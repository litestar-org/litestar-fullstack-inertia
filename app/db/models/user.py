from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .oauth_account import UserOauthAccount
    from .team_member import TeamMember
    from .user_role import UserRole


class User(UUIDAuditBase):
    __tablename__ = "user_account"
    __table_args__ = {"comment": "User accounts for application access"}
    __pii_columns__ = {"name", "email", "avatar_url", "totp_secret"}

    email: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    name: Mapped[str | None] = mapped_column(nullable=True, default=None)
    hashed_password: Mapped[str | None] = mapped_column(String(length=255), nullable=True, default=None)
    avatar_url: Mapped[str | None] = mapped_column(String(length=500), nullable=True, default=None)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    verified_at: Mapped[date] = mapped_column(nullable=True, default=None)
    joined_at: Mapped[date] = mapped_column(default=datetime.now)

    # Two-Factor Authentication (TOTP)
    totp_secret: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
        comment="Encrypted TOTP secret key for 2FA",
    )
    """Encrypted TOTP secret for generating time-based one-time passwords."""

    is_two_factor_enabled: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        comment="Whether 2FA is enabled for this user",
    )
    """Whether two-factor authentication is currently active."""

    two_factor_confirmed_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
        default=None,
        comment="When 2FA was confirmed/enabled",
    )
    """Timestamp when 2FA was successfully configured."""

    backup_codes: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
        default=None,
        comment="Hashed backup codes for 2FA recovery",
    )
    """JSON array of hashed backup codes for account recovery."""

    # -----------
    # ORM Relationships
    # ------------

    roles: Mapped[list[UserRole]] = relationship(
        back_populates="user",
        lazy="selectin",
        uselist=True,
        cascade="all, delete",
    )
    teams: Mapped[list[TeamMember]] = relationship(
        back_populates="user",
        lazy="selectin",
        uselist=True,
        cascade="all, delete",
        viewonly=True,
    )
    oauth_accounts: Mapped[list[UserOauthAccount]] = relationship(
        back_populates="user",
        lazy="noload",
        cascade="all, delete",
        uselist=True,
    )

    @hybrid_property
    def has_password(self) -> bool:
        return self.hashed_password is not None

    @hybrid_property
    def has_two_factor(self) -> bool:
        """Check if user has 2FA enabled and confirmed."""
        return self.is_two_factor_enabled and self.totp_secret is not None

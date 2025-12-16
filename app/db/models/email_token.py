"""Email token model for verification, password reset, and other token-based flows."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID  # noqa: TC003 - used at runtime for SQLAlchemy column type

from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .user import User


class TokenType(StrEnum):
    """Types of email tokens."""

    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"  # noqa: S105


class EmailToken(UUIDAuditBase):
    """Email token for verification, password reset, and similar flows.

    Tokens are single-use: once validated, `used_at` is set and the token
    cannot be reused. The actual token value is hashed (SHA-256) before
    storage - the plain token is only returned to the caller once.

    Attributes:
        user_id: The user this token is for (optional for some flows).
        email: Email address associated with this token.
        token_type: Type of token (verification, password_reset).
        token_hash: SHA-256 hash of the token (plain token never stored).
        expires_at: When this token expires.
        used_at: When the token was consumed (None if unused).
        metadata: Additional JSON data for extensibility.
    """

    __tablename__ = "email_token"
    __table_args__ = (
        Index("ix_email_token_hash", "token_hash"),
        Index("ix_email_token_email_type", "email", "token_type"),
        {"comment": "Tokens for email verification, password reset, etc."},
    )

    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("user_account.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    """User this token belongs to (nullable for pre-registration flows)."""

    email: Mapped[str] = mapped_column(String(255), nullable=False)
    """Email address this token was sent to."""

    token_type: Mapped[TokenType] = mapped_column(String(50), nullable=False)
    """Type of token (email_verification, password_reset)."""

    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    """SHA-256 hash of the token. Plain token is never stored."""

    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    """When this token expires."""

    used_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
    """When this token was used. None means unused."""

    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    """IP address where the token was requested from."""

    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    """User agent string from the request."""

    metadata_: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
    )
    """Additional metadata stored as JSON."""

    # ORM Relationships
    user: Mapped[User | None] = relationship(
        foreign_keys=[user_id],
        lazy="joined",
    )

    @property
    def is_expired(self) -> bool:
        """Check if the token has expired."""
        return datetime.now(UTC) > self.expires_at.replace(tzinfo=UTC)

    @property
    def is_used(self) -> bool:
        """Check if the token has been used."""
        return self.used_at is not None

    @property
    def is_valid(self) -> bool:
        """Check if the token is still valid (not expired and not used)."""
        return not self.is_expired and not self.is_used

    def mark_used(self) -> None:
        """Mark the token as used."""
        self.used_at = datetime.now(UTC)

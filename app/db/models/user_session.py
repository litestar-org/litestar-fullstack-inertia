from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .user import User


class UserSession(UUIDAuditBase):
    """Queryable metadata for active browser sessions."""

    __tablename__ = "user_session"
    __table_args__ = {"comment": "Track active browser sessions for account security tooling"}

    user_id: Mapped[UUID] = mapped_column(ForeignKey("user_account.id", ondelete="CASCADE"), index=True, nullable=False)
    session_id: Mapped[str] = mapped_column(String(length=255), unique=True, index=True, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(length=45), nullable=True, default=None)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    last_activity: Mapped[datetime] = mapped_column(nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(index=True, nullable=True, default=None)
    browser: Mapped[str | None] = mapped_column(String(length=100), nullable=True, default=None)
    browser_version: Mapped[str | None] = mapped_column(String(length=50), nullable=True, default=None)
    os: Mapped[str | None] = mapped_column(String(length=100), nullable=True, default=None)
    os_version: Mapped[str | None] = mapped_column(String(length=50), nullable=True, default=None)
    device_type: Mapped[str | None] = mapped_column(String(length=20), nullable=True, default=None)

    user: Mapped[User] = relationship(back_populates="sessions", lazy="joined")

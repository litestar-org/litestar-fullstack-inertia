from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .user import User


class PersonalAccessToken(UUIDAuditBase):
    """Personal access tokens for bearer authentication."""

    __tablename__ = "personal_access_token"
    __table_args__ = {"comment": "Personal access tokens for API authentication"}

    user_id: Mapped[UUID] = mapped_column(ForeignKey("user_account.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(length=255), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(length=64), unique=True, index=True, nullable=False)
    abilities: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
    expires_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)

    user: Mapped[User] = relationship(back_populates="tokens", lazy="joined")

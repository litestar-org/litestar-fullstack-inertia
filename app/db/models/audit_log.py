from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .user import User


class AuditAction(str, Enum):
    """Admin audit action types."""

    # User actions
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    USER_LOCKED = "user.locked"
    USER_UNLOCKED = "user.unlocked"
    USER_VERIFIED = "user.verified"
    USER_UNVERIFIED = "user.unverified"
    USER_ROLE_ASSIGNED = "user.role_assigned"
    USER_ROLE_REVOKED = "user.role_revoked"
    USER_PASSWORD_RESET = "user.password_reset"

    # Team actions
    TEAM_CREATED = "team.created"
    TEAM_UPDATED = "team.updated"
    TEAM_DELETED = "team.deleted"
    TEAM_MEMBER_ADDED = "team.member_added"
    TEAM_MEMBER_REMOVED = "team.member_removed"
    TEAM_MEMBER_ROLE_CHANGED = "team.member_role_changed"


class AuditLog(UUIDAuditBase):
    """Audit log for tracking administrative actions."""

    __tablename__ = "audit_log"
    __table_args__ = {"comment": "Tracks administrative actions for auditing and compliance"}

    # Actor (the admin who performed the action)
    actor_id: Mapped[UUID] = mapped_column(
        ForeignKey("user_account.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    actor_email: Mapped[str] = mapped_column(String(255), nullable=False)

    # Action type
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Target entity (polymorphic reference)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    target_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    target_label: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Additional context
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    actor: Mapped[User | None] = relationship(lazy="joined", foreign_keys=[actor_id])

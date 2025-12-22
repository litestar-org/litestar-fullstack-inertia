from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID  # noqa: TC003

from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.team_roles import TeamRoles

if TYPE_CHECKING:
    from .team import Team
    from .user import User


class TeamInvitation(UUIDAuditBase):
    """Team Invitation with secure token-based acceptance.

    Invitations are sent via email with a hashed token. The plain token
    is only sent to the invitee once. Invitations can be accepted or
    rejected, and expire after a configurable period.
    """

    __tablename__ = "team_invitation"
    __table_args__ = (
        Index("ix_team_invitation_token", "token_hash"),
        Index("ix_team_invitation_email_team", "email", "team_id"),
    )

    team_id: Mapped[UUID] = mapped_column(ForeignKey("team.id", ondelete="cascade"))
    email: Mapped[str] = mapped_column(index=True)
    role: Mapped[TeamRoles] = mapped_column(String(length=50), default=TeamRoles.MEMBER)
    is_accepted: Mapped[bool] = mapped_column(default=False)
    invited_by_id: Mapped[UUID | None] = mapped_column(ForeignKey("user_account.id", ondelete="set null"))
    invited_by_email: Mapped[str]

    # Token-based invitation security
    token_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="SHA-256 hash of invitation token",
    )
    """SHA-256 hash of the invitation token. Plain token never stored."""

    expires_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
        comment="When this invitation expires",
    )
    """Expiration timestamp for the invitation."""

    accepted_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
        default=None,
        comment="When the invitation was accepted",
    )
    """Timestamp when the invitation was accepted."""

    # -----------
    # ORM Relationships
    # ------------
    team: Mapped[Team] = relationship(foreign_keys="TeamInvitation.team_id", lazy="joined")
    invited_by: Mapped[User | None] = relationship(foreign_keys="TeamInvitation.invited_by_id", uselist=False)

    @property
    def is_expired(self) -> bool:
        """Check if the invitation has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(UTC) > self.expires_at.replace(tzinfo=UTC)

    @property
    def is_pending(self) -> bool:
        """Check if the invitation is still pending (not accepted and not expired)."""
        return not self.is_accepted and not self.is_expired

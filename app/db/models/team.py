# ruff: noqa: N802
from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.base import UUIDAuditBase
from advanced_alchemy.mixins import SlugKey
from sqlalchemy import ColumnElement, String, and_, func, or_
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.team_tag import team_tag

if TYPE_CHECKING:
    from .tag import Tag
    from .team_invitation import TeamInvitation
    from .team_member import TeamMember


class Team(UUIDAuditBase, SlugKey):
    """A group of users with common permissions.
    Users can create and invite users to a team.
    """

    __tablename__ = "team"
    __pii_columns__ = {"name", "description"}
    name: Mapped[str] = mapped_column(nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(length=500), nullable=True, default=None)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    # -----------
    # ORM Relationships
    # ------------
    members: Mapped[list[TeamMember]] = relationship(
        back_populates="team", cascade="all, delete", passive_deletes=True, lazy="selectin"
    )
    invitations: Mapped[list[TeamInvitation]] = relationship(back_populates="team", cascade="all, delete")
    pending_invitations: Mapped[list[TeamInvitation]] = relationship(
        primaryjoin=lambda: _pending_invitations_join(),
        foreign_keys=lambda: [_TeamInvitation().team_id],
        viewonly=True,
        lazy="noload",
    )
    tags: Mapped[list[Tag]] = relationship(
        secondary=lambda: team_tag, back_populates="teams", cascade="all, delete", passive_deletes=True
    )


def _TeamInvitation() -> "type[TeamInvitation]":
    """Lazy import to avoid circular dependency.

    Returns:
        TeamInvitation class.
    """
    from .team_invitation import TeamInvitation

    return TeamInvitation


def _pending_invitations_join() -> "ColumnElement[bool]":
    """Build the join condition for pending invitations.

    Filters for invitations that are:
    - Not accepted
    - Not expired (expires_at is NULL or > now())

    Returns:
        SQLAlchemy ColumnElement representing the join condition.
    """
    inv = _TeamInvitation()
    return and_(
        Team.id == inv.team_id, inv.is_accepted.is_(False), or_(inv.expires_at.is_(None), inv.expires_at > func.now())
    )

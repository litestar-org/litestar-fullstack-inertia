"""Team Dependencies."""

from __future__ import annotations

from advanced_alchemy.extensions.litestar.providers import create_service_provider
from sqlalchemy.orm import joinedload, noload, selectinload

from app.db.models import Team, TeamInvitation, TeamMember
from app.domain.teams.services import TeamInvitationService, TeamMemberService, TeamService

__all__ = ("provide_team_invitations_service", "provide_team_members_service", "provide_teams_service")


provide_teams_service = create_service_provider(
    TeamService,
    load=[
        selectinload(Team.tags),
        selectinload(Team.members).options(
            joinedload(TeamMember.user, innerjoin=True),
        ),
    ],
)

provide_team_members_service = create_service_provider(
    TeamMemberService,
    load=[
        noload("*"),
        joinedload(TeamMember.team, innerjoin=True).options(noload("*")),
        joinedload(TeamMember.user, innerjoin=True).options(noload("*")),
    ],
)

provide_team_invitations_service = create_service_provider(
    TeamInvitationService,
    load=[
        noload("*"),
        joinedload(TeamInvitation.team, innerjoin=True).options(noload("*")),
        joinedload(TeamInvitation.invited_by, innerjoin=True).options(noload("*")),
    ],
)

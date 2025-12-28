from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from litestar.events import listener

from app.config import alchemy
from app.domain.teams.dependencies import provide_teams_service
from app.lib.email import EmailService

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
    from uuid import UUID

    from app.domain.teams.services import TeamService

logger = structlog.get_logger()


@listener("team_created")
async def team_created_event_handler(team_id: UUID) -> None:
    """Executes when a new team is created.

    Args:
        team_id: The primary key of the team that was created.
    """
    await logger.ainfo("Team created.", team_id=str(team_id))

    async with alchemy.get_session() as db_session:
        service_provider: AsyncGenerator[TeamService, None] = provide_teams_service(db_session)
        try:
            service = await anext(service_provider)
            obj = await service.get_one_or_none(id=team_id)
        finally:
            await service_provider.aclose()
        if obj is None:
            await logger.aerror("Could not locate the specified team", id=team_id)
        else:
            await logger.ainfo("Found team", name=obj.name, slug=obj.slug)


@listener("team_invitation_created")
async def team_invitation_created_handler(invitee_email: str, inviter_name: str, team_name: str, token: str) -> None:
    """Executes when a team invitation is created.

    Sends an invitation email to the invitee.

    Args:
        invitee_email: Email address of the person being invited.
        inviter_name: Name of the person sending the invitation.
        team_name: Name of the team.
        token: Plain invitation token to include in the email.
    """
    await logger.ainfo("Team invitation created, sending email.", invitee_email=invitee_email, team_name=team_name)

    email_service = EmailService()
    sent = await email_service.send_team_invitation_email(
        invitee_email=invitee_email, inviter_name=inviter_name, team_name=team_name, token=token,
    )

    if sent:
        await logger.ainfo("Team invitation email sent", email=invitee_email, team=team_name)
    else:
        await logger.awarning("Failed to send team invitation email", email=invitee_email, team=team_name)

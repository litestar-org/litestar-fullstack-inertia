"""User's pending invitations controller."""

from __future__ import annotations

from advanced_alchemy.extensions.litestar.providers import create_service_provider
from litestar import Controller, get
from sqlalchemy.orm import joinedload

from app.db.models import TeamInvitation as TeamInvitationModel
from app.db.models import User as UserModel
from app.domain.accounts.guards import requires_active_user
from app.domain.teams.schemas import UserPendingInvitation, UserPendingInvitationsPage
from app.domain.teams.services import TeamInvitationService

__all__ = ("UserInvitationsController",)


class UserInvitationsController(Controller):
    """User's pending invitations."""

    tags = ["Teams"]
    guards = [requires_active_user]
    dependencies = {
        "team_invitations_service": create_service_provider(
            TeamInvitationService,
            load=[
                joinedload(TeamInvitationModel.team),
                joinedload(TeamInvitationModel.invited_by),
            ],
        ),
    }
    signature_namespace = {
        "TeamInvitationService": TeamInvitationService,
    }

    @get(
        component="invitation/list",
        name="invitations.list",
        operation_id="GetUserInvitations",
        path="/invitations/",
    )
    async def get_user_invitations(
        self,
        team_invitations_service: TeamInvitationService,
        current_user: UserModel,
    ) -> UserPendingInvitationsPage:
        """Get all pending invitations for the current user.

        Returns:
            List of pending invitations.
        """
        invitations = await team_invitations_service.get_pending_for_email(current_user.email)

        return UserPendingInvitationsPage(
            invitations=[
                UserPendingInvitation(
                    id=inv.id,
                    team_name=inv.team.name,
                    team_slug=inv.team.slug,
                    inviter_name=(inv.invited_by.name if inv.invited_by and inv.invited_by.name else None) or inv.invited_by_email or "",
                    role=str(inv.role),
                    created_at=inv.created_at,
                )
                for inv in invitations
            ],
        )

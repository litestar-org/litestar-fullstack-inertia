"""Team invitation controller."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from advanced_alchemy.extensions.litestar.providers import create_service_provider
from litestar import Controller, Request, delete, get, post
from litestar.params import Parameter
from litestar_vite.inertia import InertiaRedirect, flash
from sqlalchemy.orm import joinedload, selectinload

from app.db.models import Team as TeamModel
from app.db.models import TeamInvitation as TeamInvitationModel
from app.db.models import TeamMember, TeamRoles
from app.db.models import User as UserModel
from app.domain.accounts.guards import requires_active_user
from app.domain.teams.guards import requires_team_admin
from app.domain.teams.schemas import (
    CurrentTeam,
    TeamDetail,
    TeamInvitationCreate,
    TeamInvitationItem,
    TeamInvitationsPage,
    TeamPermissions,
)
from app.domain.teams.services import TeamInvitationService, TeamMemberService, TeamService

if TYPE_CHECKING:
    from uuid import UUID

__all__ = ("TeamInvitationController",)


class TeamInvitationController(Controller):
    """Team Invitations."""

    tags = ["Teams"]
    guards = [requires_active_user]
    dependencies = {
        "teams_service": create_service_provider(
            TeamService,
            load=[
                selectinload(TeamModel.tags),
                selectinload(TeamModel.members).options(
                    joinedload(TeamMember.user, innerjoin=True),
                ),
            ],
        ),
        "team_invitations_service": create_service_provider(
            TeamInvitationService,
            load=[
                joinedload(TeamInvitationModel.team),
                joinedload(TeamInvitationModel.invited_by),
            ],
        ),
        "team_members_service": create_service_provider(TeamMemberService),
    }
    signature_namespace = {
        "TeamService": TeamService,
        "TeamInvitationService": TeamInvitationService,
        "TeamMemberService": TeamMemberService,
        "TeamInvitationCreate": TeamInvitationCreate,
    }

    @get(
        component="team/invitations",
        name="teams.invitations",
        operation_id="GetTeamInvitations",
        guards=[requires_team_admin],
        path="/teams/{team_slug:str}/invitations/",
    )
    async def get_team_invitations(
        self,
        request: Request,
        teams_service: TeamService,
        team_invitations_service: TeamInvitationService,
        current_user: UserModel,
        team_slug: Annotated[str, Parameter(title="Team Slug", description="The team slug.")],
    ) -> TeamInvitationsPage:
        """Get pending invitations for a team.

        Returns:
            Team details and list of pending invitations.
        """
        db_obj = await teams_service.get_one(slug=team_slug)
        request.session.update({"currentTeam": CurrentTeam(team_id=db_obj.id, team_name=db_obj.name)})

        invitations = await team_invitations_service.get_pending_for_team(db_obj.id)

        membership = next((m for m in db_obj.members if m.user_id == current_user.id), None)
        is_owner = bool(membership and membership.is_owner)
        is_admin = is_owner or bool(membership and membership.role == TeamRoles.ADMIN)

        return TeamInvitationsPage(
            team=TeamDetail(
                id=db_obj.id,
                name=db_obj.name,
                slug=db_obj.slug,
                description=db_obj.description,
            ),
            invitations=[
                TeamInvitationItem(
                    id=inv.id,
                    email=inv.email,
                    role=str(inv.role),
                    invited_by_email=inv.invited_by_email,
                    created_at=inv.created_at,
                    expires_at=inv.expires_at,
                    is_expired=inv.is_expired,
                )
                for inv in invitations
            ],
            permissions=TeamPermissions(
                can_add_team_members=is_admin,
                can_delete_team=is_owner,
                can_remove_team_members=is_admin,
                can_update_team=is_admin,
            ),
        )

    @post(
        name="teams.invite",
        operation_id="CreateTeamInvitation",
        guards=[requires_team_admin],
        path="/teams/{team_slug:str}/invitations/",
    )
    async def create_invitation(
        self,
        request: Request,
        teams_service: TeamService,
        team_invitations_service: TeamInvitationService,
        current_user: UserModel,
        data: TeamInvitationCreate,
        team_slug: Annotated[str, Parameter(title="Team Slug", description="The team slug.")],
    ) -> InertiaRedirect:
        """Create a new team invitation.

        Returns:
            Redirect to invitations page.
        """
        team_obj = await teams_service.get_one(slug=team_slug)

        is_member = any(m.user.email == data.email for m in team_obj.members)
        if is_member:
            flash(request, "This user is already a member of the team.", category="error")
            return InertiaRedirect(request, request.url_for("teams.invitations", team_slug=team_slug))

        has_pending = await team_invitations_service.has_pending_invitation(team_obj.id, data.email)
        if has_pending:
            flash(request, "An invitation has already been sent to this email.", category="error")
            return InertiaRedirect(request, request.url_for("teams.invitations", team_slug=team_slug))

        _, token = await team_invitations_service.create_invitation(
            team=team_obj,
            email=data.email,
            role=data.role,
            invited_by=current_user,
        )

        request.app.emit(
            "team_invitation_created",
            invitee_email=data.email,
            inviter_name=current_user.name or current_user.email,
            team_name=team_obj.name,
            token=token,
        )

        flash(request, f"Invitation sent to {data.email}.", category="info")
        return InertiaRedirect(request, request.url_for("teams.invitations", team_slug=team_slug))

    @delete(
        name="teams.invitation.cancel",
        operation_id="CancelTeamInvitation",
        guards=[requires_team_admin],
        path="/teams/{team_slug:str}/invitations/{invitation_id:uuid}",
        status_code=303,
    )
    async def cancel_invitation(
        self,
        request: Request,
        team_invitations_service: TeamInvitationService,
        team_slug: Annotated[str, Parameter(title="Team Slug", description="The team slug.")],
        invitation_id: Annotated[UUID, Parameter(title="Invitation ID", description="The invitation ID.")],
    ) -> InertiaRedirect:
        """Cancel a pending invitation.

        Returns:
            Redirect to invitations page.
        """
        await team_invitations_service.delete(invitation_id)
        flash(request, "Invitation cancelled.", category="info")
        return InertiaRedirect(request, request.url_for("teams.invitations", team_slug=team_slug))

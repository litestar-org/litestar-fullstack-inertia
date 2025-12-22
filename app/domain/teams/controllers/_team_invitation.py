"""Team invitation controller."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from advanced_alchemy.extensions.litestar.providers import create_service_provider
from litestar import Controller, Request, delete, get, post
from litestar.di import Provide
from litestar.exceptions import PermissionDeniedException
from litestar.params import Parameter
from litestar_vite.inertia import InertiaRedirect, flash
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

from app.db.models import Team as TeamModel
from app.db.models import TeamInvitation as TeamInvitationModel
from app.db.models import TeamMember, TeamRoles
from app.db.models import User as UserModel
from app.domain.accounts.dependencies import provide_users_service
from app.domain.accounts.guards import requires_active_user
from app.domain.accounts.services import UserService
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
                selectinload(TeamModel.members).options(joinedload(TeamMember.user, innerjoin=True)),
            ],
        ),
        "team_invitations_service": create_service_provider(
            TeamInvitationService,
            load=[joinedload(TeamInvitationModel.team), joinedload(TeamInvitationModel.invited_by)],
        ),
        "team_members_service": create_service_provider(TeamMemberService),
        "users_service": Provide(provide_users_service),
    }
    signature_namespace = {
        "TeamService": TeamService,
        "TeamInvitationService": TeamInvitationService,
        "TeamMemberService": TeamMemberService,
        "TeamInvitationCreate": TeamInvitationCreate,
        "UserService": UserService,
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
        users_service: UserService,
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

        invitee_flags: dict[str, bool] = {}
        if invitations:
            emails = {inv.email for inv in invitations}
            result = await users_service.repository.session.execute(
                select(UserModel.email).where(UserModel.email.in_(emails)),
            )
            existing_emails = {row[0] for row in result}
            invitee_flags = {email: email in existing_emails for email in emails}

        return TeamInvitationsPage(
            team=TeamDetail(id=db_obj.id, name=db_obj.name, slug=db_obj.slug, description=db_obj.description),
            invitations=[
                TeamInvitationItem(
                    id=inv.id,
                    email=inv.email,
                    role=str(inv.role),
                    invited_by_email=inv.invited_by_email,
                    created_at=inv.created_at,
                    expires_at=inv.expires_at,
                    is_expired=inv.is_expired,
                    invitee_exists=invitee_flags.get(inv.email, False),
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
        users_service: UserService,
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

        invitee = await users_service.get_one_or_none(email=data.email)

        _, token = await team_invitations_service.create_invitation(
            team=team_obj, email=data.email, role=data.role, invited_by=current_user,
        )

        request.app.emit(
            "team_invitation_created",
            invitee_email=data.email,
            inviter_name=current_user.name or current_user.email,
            team_name=team_obj.name,
            token=token,
        )

        if invitee:
            flash(
                request,
                f"{data.email} is already registered. Invitation sent to join {team_obj.name}.",
                category="success",
            )
        else:
            flash(request, f"{data.email} was invited to sign up and join {team_obj.name}.", category="success")

        redirect_target = request.headers.get("referer") or request.url_for("teams.invitations", team_slug=team_slug)
        return InertiaRedirect(request, redirect_target)

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

        Raises:
            PermissionDeniedException: If the invitation does not belong to the team.

        Returns:
            Redirect to invitations page.
        """
        invitation = await team_invitations_service.get_one_or_none(id=invitation_id)
        if invitation is None or invitation.team.slug != team_slug:
            msg = "Invitation does not belong to this team."
            raise PermissionDeniedException(detail=msg)
        await team_invitations_service.delete(invitation_id)
        flash(request, "Invitation cancelled.", category="info")
        return InertiaRedirect(request, request.url_for("teams.invitations", team_slug=team_slug))

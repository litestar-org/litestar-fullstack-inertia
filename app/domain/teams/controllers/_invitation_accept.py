"""Invitation accept/decline controller."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from advanced_alchemy.exceptions import RepositoryError
from advanced_alchemy.extensions.litestar.providers import create_service_provider
from litestar import Controller, Request, get, post
from litestar.params import Parameter
from litestar_vite.inertia import InertiaRedirect, flash
from sqlalchemy.orm import joinedload

from app.db.models import TeamInvitation as TeamInvitationModel
from app.db.models import User as UserModel
from app.domain.accounts.guards import requires_active_user
from app.domain.teams.schemas import InvitationAcceptPage, TeamInvitationDetail
from app.domain.teams.services import TeamInvitationService, TeamMemberService

__all__ = ("InvitationAcceptController",)


class InvitationAcceptController(Controller):
    """Accept/Decline invitations (token-based, GET works without auth, POST requires auth)."""

    tags = ["Teams"]
    dependencies = {
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
        "TeamInvitationService": TeamInvitationService,
        "TeamMemberService": TeamMemberService,
    }

    @get(
        component="invitation/accept",
        name="invitation.accept.page",
        operation_id="GetInvitationAcceptPage",
        path="/invitations/{token:str}/",
        exclude_from_auth=True,
    )
    async def get_invitation_page(
        self,
        request: Request,
        team_invitations_service: TeamInvitationService,
        token: Annotated[str, Parameter(title="Token", description="The invitation token.")],
    ) -> InvitationAcceptPage:
        """Show invitation accept/decline page.

        Works for both authenticated and unauthenticated users.
        Unauthenticated users see the invitation details and can log in or sign up.

        Returns:
            Invitation details and validity status.
        """
        invitation = await team_invitations_service.get_by_token(token)

        request.session["invitation_token"] = token

        user_id = request.session.get("user_id")
        is_authenticated = user_id is not None
        current_user_email = user_id if is_authenticated else None

        login_url = str(request.url_for("login"))
        register_url = str(request.url_for("register"))

        if invitation is None:
            return InvitationAcceptPage(
                invitation=TeamInvitationDetail(
                    id=UUID("00000000-0000-0000-0000-000000000000"),
                    team_name="",
                    team_slug="",
                    inviter_name="",
                    inviter_email="",
                    role="",
                ),
                is_valid=False,
                error_message="This invitation link is invalid or has been revoked.",
                is_authenticated=is_authenticated,
                is_correct_user=False,
                login_url=login_url,
                register_url=register_url,
            )

        inviter_name = (invitation.invited_by.name if invitation.invited_by and invitation.invited_by.name else None) or invitation.invited_by_email or ""
        base_detail = TeamInvitationDetail(
            id=invitation.id,
            team_name=invitation.team.name,
            team_slug=invitation.team.slug,
            inviter_name=inviter_name,
            inviter_email=invitation.invited_by_email,
            role=str(invitation.role),
            expires_at=invitation.expires_at,
        )

        if invitation.is_expired:
            return InvitationAcceptPage(
                invitation=TeamInvitationDetail(
                    **{**base_detail.to_dict(), "is_expired": True},
                ),
                is_valid=False,
                error_message="This invitation has expired.",
                is_authenticated=is_authenticated,
                is_correct_user=False,
                login_url=login_url,
                register_url=register_url,
            )

        if invitation.is_accepted:
            return InvitationAcceptPage(
                invitation=base_detail,
                is_valid=False,
                error_message="This invitation has already been accepted.",
                is_authenticated=is_authenticated,
                is_correct_user=False,
                login_url=login_url,
                register_url=register_url,
            )

        if not is_authenticated:
            return InvitationAcceptPage(
                invitation=base_detail,
                is_valid=True,
                is_authenticated=False,
                is_correct_user=False,
                login_url=login_url,
                register_url=register_url,
            )

        is_correct_user = current_user_email == invitation.email
        if not is_correct_user:
            return InvitationAcceptPage(
                invitation=base_detail,
                is_valid=False,
                error_message=f"This invitation was sent to {invitation.email}. Please log in with that account.",
                is_authenticated=True,
                is_correct_user=False,
                login_url=login_url,
                register_url=register_url,
            )

        return InvitationAcceptPage(
            invitation=base_detail,
            is_valid=True,
            is_authenticated=True,
            is_correct_user=True,
            login_url=login_url,
            register_url=register_url,
        )

    @post(
        name="invitation.accept",
        operation_id="AcceptInvitation",
        path="/invitations/{token:str}/accept",
        guards=[requires_active_user],
    )
    async def accept_invitation(
        self,
        request: Request,
        team_invitations_service: TeamInvitationService,
        team_members_service: TeamMemberService,
        current_user: UserModel,
        token: Annotated[str, Parameter(title="Token", description="The invitation token.")],
    ) -> InertiaRedirect:
        """Accept a team invitation.

        Returns:
            Redirect to the team page.
        """
        invitation = await team_invitations_service.get_by_token(token)

        if invitation is None:
            flash(request, "Invalid invitation.", category="error")
            return InertiaRedirect(request, request.url_for("dashboard"))

        if current_user.email != invitation.email:
            flash(request, f"This invitation was sent to {invitation.email}.", category="error")
            return InertiaRedirect(request, request.url_for("dashboard"))

        try:
            await team_invitations_service.accept_invitation(
                invitation=invitation,
                user=current_user,
                team_member_service=team_members_service,
            )
            request.session.pop("invitation_token", None)
            flash(request, f"You have joined {invitation.team.name}!", category="info")
            return InertiaRedirect(request, request.url_for("teams.show", team_slug=invitation.team.slug))
        except RepositoryError as e:
            flash(request, str(e), category="error")
            return InertiaRedirect(request, request.url_for("dashboard"))

    @post(
        name="invitation.decline",
        operation_id="DeclineInvitation",
        path="/invitations/{token:str}/decline",
        guards=[requires_active_user],
    )
    async def decline_invitation(
        self,
        request: Request,
        team_invitations_service: TeamInvitationService,
        current_user: UserModel,
        token: Annotated[str, Parameter(title="Token", description="The invitation token.")],
    ) -> InertiaRedirect:
        """Decline a team invitation.

        Returns:
            Redirect to dashboard.
        """
        invitation = await team_invitations_service.get_by_token(token)

        if invitation is None:
            flash(request, "Invalid invitation.", category="error")
            return InertiaRedirect(request, request.url_for("dashboard"))

        if current_user.email != invitation.email:
            flash(request, f"This invitation was sent to {invitation.email}.", category="error")
            return InertiaRedirect(request, request.url_for("dashboard"))

        await team_invitations_service.delete(invitation.id)
        request.session.pop("invitation_token", None)
        flash(request, "Invitation declined.", category="info")
        return InertiaRedirect(request, request.url_for("dashboard"))

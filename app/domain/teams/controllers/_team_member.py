"""Team member controller."""

from __future__ import annotations

from typing import Annotated

from advanced_alchemy.extensions.litestar.providers import create_service_provider
from litestar import Controller, Request, post
from litestar.di import Provide
from litestar.exceptions import ValidationException
from litestar.params import Parameter
from sqlalchemy.orm import joinedload, noload, selectinload

from app.db.models import Team as TeamModel
from app.db.models import TeamInvitation as TeamInvitationModel
from app.db.models import TeamMember, TeamRoles
from app.db.models import User as UserModel
from app.domain.accounts.dependencies import provide_users_service
from app.domain.accounts.guards import requires_active_user
from app.domain.accounts.services import UserService
from app.domain.teams.guards import requires_team_admin
from app.domain.teams.schemas import Team, TeamMemberModify
from app.domain.teams.services import TeamInvitationService, TeamMemberService, TeamService
from app.lib.schema import Message

__all__ = ("TeamMemberController",)

# Exception messages
_MSG_USER_NOT_FOUND = "User not found"
_MSG_USER_ALREADY_MEMBER = "User is already a member of the team"
_MSG_USER_NOT_MEMBER = "User is not a member of this team"
_MSG_INVITATION_PENDING = "An invitation has already been sent to this email"


class TeamMemberController(Controller):
    """Team Members."""

    tags = ["Team Members"]
    guards = [requires_active_user, requires_team_admin]
    dependencies = {
        "teams_service": create_service_provider(
            TeamService,
            load=[
                selectinload(TeamModel.tags),
                selectinload(TeamModel.members).options(joinedload(TeamMember.user, innerjoin=True)),
            ],
        ),
        "team_members_service": create_service_provider(
            TeamMemberService,
            load=[
                noload("*"),
                joinedload(TeamMember.team, innerjoin=True).options(noload("*")),
                joinedload(TeamMember.user, innerjoin=True).options(noload("*")),
            ],
        ),
        "team_invitations_service": create_service_provider(
            TeamInvitationService, load=[TeamInvitationModel.team, TeamInvitationModel.invited_by],
        ),
        "users_service": Provide(provide_users_service),
    }
    signature_namespace = {
        "TeamService": TeamService,
        "UserService": UserService,
        "TeamMemberService": TeamMemberService,
        "TeamInvitationService": TeamInvitationService,
        "Team": Team,
    }

    @post(operation_id="AddMemberToTeam", name="teams:add-member", path="/api/teams/{team_slug:str}/members/add")
    async def add_member_to_team(
        self,
        request: Request,
        teams_service: TeamService,
        team_members_service: TeamMemberService,
        team_invitations_service: TeamInvitationService,
        users_service: UserService,
        current_user: UserModel,
        data: TeamMemberModify,
        team_slug: Annotated[str, Parameter(title="Team Slug", description="The team slug.")],
    ) -> Message:
        """Add a member to a team, or send an invitation if the user doesn't exist.

        If the user exists in the system, they are added directly as a team member.
        If the user doesn't exist, an invitation email is sent to them to sign up
        and join the team.

        Returns:
            Message describing whether the user was added or invited.

        Raises:
            ValidationException: If the user is already a member or has a pending invitation.
        """
        team_obj = await teams_service.get_one(slug=team_slug)
        user_obj = await users_service.get_one_or_none(email=data.user_name)

        if user_obj:
            is_member = any(membership.team_id == team_obj.id for membership in user_obj.teams)
            if is_member:
                raise ValidationException(_MSG_USER_ALREADY_MEMBER)
            await team_members_service.create({
                "team_id": team_obj.id,
                "user_id": user_obj.id,
                "role": TeamRoles.MEMBER,
            })
            message = f"{data.user_name} is already registered and was added to {team_obj.name}."
        else:
            # User doesn't exist - create an invitation
            # Check if invitation already pending
            has_pending = await team_invitations_service.has_pending_invitation(team_obj.id, data.user_name)
            if has_pending:
                raise ValidationException(_MSG_INVITATION_PENDING)
            _, token = await team_invitations_service.create_invitation(
                team=team_obj, email=data.user_name, role=TeamRoles.MEMBER, invited_by=current_user,
            )
            request.app.emit(
                "team_invitation_created",
                invitee_email=data.user_name,
                inviter_name=current_user.name or current_user.email,
                team_name=team_obj.name,
                token=token,
            )
            message = f"{data.user_name} was invited to sign up and join {team_obj.name}."

        return Message(message=message)

    @post(
        operation_id="RemoveMemberFromTeam",
        name="teams:remove-member",
        summary="Remove Team Member",
        description="Removes a member from a team",
        path="/api/teams/{team_slug:str}/members/remove",
        status_code=200,
    )
    async def remove_member_from_team(
        self,
        teams_service: TeamService,
        team_members_service: TeamMemberService,
        users_service: UserService,
        data: TeamMemberModify,
        team_slug: Annotated[str, Parameter(title="Team Slug", description="The team slug.")],
    ) -> Team:
        """Remove a member from a team.

        Returns:
            Updated team data without the removed member.

        Raises:
            ValidationException: If the user is not found or not a member of this team.
        """
        team_obj = await teams_service.get_one(slug=team_slug)
        user_obj = await users_service.get_one_or_none(email=data.user_name)
        if not user_obj:
            raise ValidationException(_MSG_USER_NOT_FOUND)
        membership = next((membership for membership in user_obj.teams if membership.team_id == team_obj.id), None)
        if not membership:
            raise ValidationException(_MSG_USER_NOT_MEMBER)
        _ = await team_members_service.delete(membership.id)
        team_obj = await teams_service.get_one(slug=team_slug)
        return teams_service.to_schema(schema_type=Team, data=team_obj)

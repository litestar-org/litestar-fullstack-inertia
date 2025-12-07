"""Team Controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from advanced_alchemy.exceptions import IntegrityError
from litestar import Controller, Request, delete, get, patch, post
from litestar.di import Provide
from litestar.params import Parameter
from litestar.plugins.flash import flash
from litestar_vite.inertia import InertiaRedirect
from sqlalchemy import select

from app.db.models import Team as TeamModel
from app.db.models import TeamMember, TeamRoles
from app.db.models import User as UserModel
from app.db.models.team_member import TeamMember as TeamMemberModel
from app.domain.accounts.dependencies import provide_users_service
from app.domain.accounts.guards import requires_active_user
from app.domain.accounts.services import UserService
from app.domain.teams.dependencies import (
    provide_team_invitations_service,
    provide_team_members_service,
    provide_teams_service,
)
from app.domain.teams.guards import requires_team_admin, requires_team_membership, requires_team_ownership
from app.domain.teams.schemas import Team, TeamCreate, TeamMemberModify, TeamUpdate
from app.domain.teams.services import TeamMemberService, TeamService

if TYPE_CHECKING:
    from uuid import UUID

    from advanced_alchemy.service.pagination import OffsetPagination
    from litestar.params import Dependency

    from app.lib.dependencies import FilterTypes


class TeamController(Controller):
    """Teams."""

    tags = ["Teams"]
    dependencies = {"teams_service": Provide(provide_teams_service)}
    guards = [requires_active_user]
    signature_namespace = {
        "TeamService": TeamService,
        "TeamUpdate": TeamUpdate,
        "TeamCreate": TeamCreate,
    }

    @get(
        component="team/list",
        name="teams.list",
        operation_id="ListTeams",
        path="/teams/",
    )
    async def list_teams(
        self,
        teams_service: TeamService,
        current_user: UserModel,
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> OffsetPagination[Team]:
        """List teams that your account can access.."""
        if not teams_service.can_view_all(current_user):
            filters.append(
                TeamModel.id.in_(select(TeamMemberModel.team_id).where(TeamMemberModel.user_id == current_user.id)),  # type: ignore[arg-type]
            )
        results, total = await teams_service.list_and_count(*filters)
        return teams_service.to_schema(data=results, total=total, schema_type=Team, filters=filters)

    @post(
        name="teams.add",
        operation_id="CreateTeam",
        summary="Create a new team.",
        path="/teams/",
    )
    async def create_team(
        self,
        request: Request,
        teams_service: TeamService,
        current_user: UserModel,
        data: TeamCreate,
    ) -> InertiaRedirect:
        """Create a new team."""
        obj = data.to_dict()
        obj.update({"owner_id": current_user.id, "owner": current_user})
        db_obj = await teams_service.create(obj)
        flash(request, f'Successfully created team "{db_obj.name}".', category="info")
        return InertiaRedirect(request, request.url_for("teams.show", team_id=db_obj.id))

    @get(
        component="team/show",
        name="teams.show",
        operation_id="GetTeam",
        guards=[requires_team_membership],
        path="/teams/{team_id:uuid}/",
    )
    async def get_team(
        self,
        request: Request,
        teams_service: TeamService,
        team_id: Annotated[
            UUID,
            Parameter(
                title="Team ID",
                description="The team to retrieve.",
            ),
        ],
    ) -> Team:
        """Get details about a team."""
        db_obj = await teams_service.get(team_id)
        request.session.update({"currentTeam": {"teamId": db_obj.id, "teamName": db_obj.name}})
        return teams_service.to_schema(schema_type=Team, data=db_obj)

    @patch(
        component="team/edit",
        name="teams.edit",
        operation_id="UpdateTeam",
        guards=[requires_team_admin],
        path="/teams/{team_id:uuid}/",
    )
    async def update_team(
        self,
        request: Request,
        data: TeamUpdate,
        teams_service: TeamService,
        team_id: Annotated[
            UUID,
            Parameter(
                title="Team ID",
                description="The team to update.",
            ),
        ],
    ) -> Team:
        """Update a migration team."""
        db_obj = await teams_service.update(
            item_id=team_id,
            data=data.to_dict(),
        )
        request.session.update({"currentTeam": {"teamId": db_obj.id, "teamName": db_obj.name}})
        return teams_service.to_schema(schema_type=Team, data=db_obj)

    @delete(
        name="teams.remove",
        operation_id="DeleteTeam",
        guards=[requires_team_ownership],
        path="/teams/{team_id:uuid}/",
        status_code=303,  # This is the correct inertia redirect code
    )
    async def delete_team(
        self,
        request: Request,
        teams_service: TeamService,
        team_id: Annotated[
            UUID,
            Parameter(title="Team ID", description="The team to delete."),
        ],
    ) -> InertiaRedirect:
        """Delete a team."""
        request.session.pop("currentTeam", None)
        db_obj = await teams_service.delete(team_id)
        flash(request, f'Removed team "{db_obj.name}".', category="info")
        return InertiaRedirect(request, request.url_for("teams.list"))


class TeamMemberController(Controller):
    """Team Members."""

    tags = ["Team Members"]
    dependencies = {
        "teams_service": Provide(provide_teams_service),
        "team_members_service": Provide(provide_team_members_service),
        "users_service": Provide(provide_users_service),
    }
    signature_namespace = {
        "TeamService": TeamService,
        "UserService": UserService,
        "TeamMemberService": TeamMemberService,
    }

    @post(
        operation_id="AddMemberToTeam",
        name="teams:add-member",
        path="/api/teams/{team_id:uuid}/members/add",
    )
    async def add_member_to_team(
        self,
        teams_service: TeamService,
        users_service: UserService,
        data: TeamMemberModify,
        team_id: UUID = Parameter(
            title="Team ID",
            description="The team to update.",
        ),
    ) -> Team:
        """Add a member to a team.

        Raises:
            IntegrityError: If the user is already a member of the team.
        """
        team_obj = await teams_service.get(team_id)
        user_obj = await users_service.get_one(email=data.user_name)
        is_member = any(membership.team.id == team_id for membership in user_obj.teams)
        if is_member:
            msg = "User is already a member of the team."
            raise IntegrityError(msg)
        team_obj.members.append(TeamMember(user_id=user_obj.id, role=TeamRoles.MEMBER))
        team_obj = await teams_service.update(item_id=team_id, data=team_obj)
        return teams_service.to_schema(schema_type=Team, data=team_obj)

    @post(
        operation_id="RemoveMemberFromTeam",
        name="teams:remove-member",
        summary="Remove Team Member",
        description="Removes a member from a team",
        path="/api/teams/{team_id:uuid}/members/remove",
    )
    async def remove_member_from_team(
        self,
        teams_service: TeamService,
        team_members_service: TeamMemberService,
        users_service: UserService,
        data: TeamMemberModify,
        team_id: UUID = Parameter(
            title="Team ID",
            description="The team to delete.",
        ),
    ) -> Team:
        """Remove a member from a team.

        Raises:
            IntegrityError: If the user is not a member of this team.
        """
        user_obj = await users_service.get_one(email=data.user_name)
        removed_member = False
        for membership in user_obj.teams:
            if membership.user_id == user_obj.id:
                removed_member = True
                _ = await team_members_service.delete(membership.id)
        if not removed_member:
            msg = "User is not a member of this team."
            raise IntegrityError(msg)
        team_obj = await teams_service.get(team_id)
        return teams_service.to_schema(schema_type=Team, data=team_obj)


class TeamInvitationController(Controller):
    """Team Invitations."""

    tags = ["Teams"]
    dependencies = {"team_invitations_service": Provide(provide_team_invitations_service)}

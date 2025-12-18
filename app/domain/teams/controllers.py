"""Team Controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from advanced_alchemy.exceptions import IntegrityError
from advanced_alchemy.extensions.litestar.providers import create_service_dependencies, create_service_provider
from litestar import Controller, Request, delete, get, patch, post
from litestar.di import Provide
from litestar.params import Dependency, Parameter
from litestar_vite.inertia import InertiaRedirect, flash
from sqlalchemy import select
from sqlalchemy.orm import joinedload, noload, selectinload

from app.db.models import Team as TeamModel
from app.db.models import TeamMember, TeamRoles
from app.db.models import User as UserModel
from app.db.models.team_member import TeamMember as TeamMemberModel
from app.domain.accounts.dependencies import provide_users_service
from app.domain.accounts.guards import requires_active_user
from app.domain.accounts.services import UserService
from app.domain.teams.guards import requires_team_admin, requires_team_membership, requires_team_ownership
from app.domain.teams.schemas import CurrentTeam, Team, TeamCreate, TeamMemberModify, TeamUpdate
from app.domain.teams.services import TeamInvitationService, TeamMemberService, TeamService
from app.lib.schema import NoProps

if TYPE_CHECKING:
    from advanced_alchemy.filters import FilterTypes


class TeamController(Controller):
    """Teams."""

    tags = ["Teams"]
    dependencies = create_service_dependencies(
        TeamService,
        key="teams_service",
        load=[
            selectinload(TeamModel.tags),
            selectinload(TeamModel.members).options(
                joinedload(TeamMember.user, innerjoin=True),
            ),
        ],
        filters={
            "id_filter": UUID,
            "search": "name",
            "pagination_type": "limit_offset",
            "pagination_size": 20,
            "created_at": True,
            "updated_at": True,
            "sort_field": "name",
            "sort_order": "asc",
        },
    )
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
    ) -> dict:
        """List teams that your account can access.

        Returns:
            Teams list with user roles and total count.
        """
        if not teams_service.can_view_all(current_user):
            filters.append(
                TeamModel.id.in_(select(TeamMemberModel.team_id).where(TeamMemberModel.user_id == current_user.id)),  # type: ignore[arg-type]
            )
        results, total = await teams_service.list_and_count(*filters)

        # Build teams list with user's role per team
        teams_with_roles = []
        for team in results:
            user_membership = next(
                (m for m in team.members if m.user_id == current_user.id),
                None,
            )
            user_role = (
                "owner" if user_membership.is_owner else str(user_membership.role)
            ) if user_membership else "member"

            teams_with_roles.append(
                {
                    "id": str(team.id),
                    "name": team.name,
                    "description": team.description,
                    "slug": team.slug,
                    "memberCount": len(team.members),
                    "userRole": user_role,
                    "createdAt": team.created_at.isoformat() if team.created_at else None,
                },
            )

        return {"teams": teams_with_roles, "total": total}

    @get(
        component="team/create",
        name="teams.create",
        operation_id="CreateTeamPage",
        path="/teams/create/",
    )
    async def create_team_page(self) -> NoProps:
        """Show team creation page.

        Returns:
            Empty page props.
        """
        return NoProps()

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
        """Create a new team.

        Returns:
            Redirect to the newly created team's detail page.
        """
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
        current_user: UserModel,
        team_id: Annotated[UUID, Parameter(title="Team ID", description="The team to retrieve.")],
    ) -> dict:
        """Get details about a team.

        Returns:
            Team details, members list, and user permissions.
        """
        db_obj = await teams_service.get(team_id)
        request.session.update({"currentTeam": CurrentTeam(team_id=str(db_obj.id), team_name=db_obj.name)})

        # Determine user's permissions
        user_membership = next(
            (m for m in db_obj.members if m.user_id == current_user.id),
            None,
        )
        is_owner = user_membership.is_owner if user_membership else False
        is_admin = is_owner or (user_membership and user_membership.role == TeamRoles.ADMIN)

        # Build members list with proper structure
        members = []
        for member in db_obj.members:
            role = "owner" if member.is_owner else str(member.role)
            members.append(
                {
                    "id": str(member.id),
                    "userId": str(member.user_id),
                    "name": member.user.name,
                    "email": member.user.email,
                    "avatarUrl": member.user.avatar_url,
                    "role": role,
                },
            )

        return {
            "team": {
                "id": str(db_obj.id),
                "name": db_obj.name,
                "description": db_obj.description,
                "slug": db_obj.slug,
            },
            "members": members,
            "permissions": {
                "canAddTeamMembers": is_admin,
                "canDeleteTeam": is_owner,
                "canRemoveTeamMembers": is_admin,
                "canUpdateTeam": is_admin,
            },
        }

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
        team_id: Annotated[UUID, Parameter(title="Team ID", description="The team to update.")],
    ) -> Team:
        """Update a migration team.

        Returns:
            Updated team data.
        """
        db_obj = await teams_service.update(
            item_id=team_id,
            data=data.to_dict(),
        )
        request.session.update({"currentTeam": CurrentTeam(team_id=str(db_obj.id), team_name=db_obj.name)})
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
        team_id: Annotated[UUID, Parameter(title="Team ID", description="The team to delete.")],
    ) -> InertiaRedirect:
        """Delete a team.

        Returns:
            Redirect to teams list page.
        """
        request.session.pop("currentTeam", None)
        db_obj = await teams_service.delete(team_id)
        flash(request, f'Removed team "{db_obj.name}".', category="info")
        return InertiaRedirect(request, request.url_for("teams.list"))


class TeamMemberController(Controller):
    """Team Members."""

    tags = ["Team Members"]
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
        "team_members_service": create_service_provider(
            TeamMemberService,
            load=[
                noload("*"),
                joinedload(TeamMember.team, innerjoin=True).options(noload("*")),
                joinedload(TeamMember.user, innerjoin=True).options(noload("*")),
            ],
        ),
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
        team_id: Annotated[UUID, Parameter(title="Team ID", description="The team to update.")],
    ) -> Team:
        """Add a member to a team.

        Returns:
            Updated team data with new member.

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
        team_id: Annotated[UUID, Parameter(title="Team ID", description="The team to delete.")],
    ) -> Team:
        """Remove a member from a team.

        Returns:
            Updated team data without the removed member.

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
    dependencies = create_service_dependencies(
        TeamInvitationService,
        key="team_invitations_service",
    )

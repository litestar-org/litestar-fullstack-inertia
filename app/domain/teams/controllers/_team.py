"""Team controller."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from advanced_alchemy.extensions.litestar.providers import create_service_dependencies, create_service_provider
from litestar import Controller, Request, delete, get, patch, post
from litestar.di import Provide
from litestar.params import Dependency, Parameter
from litestar_vite.inertia import InertiaRedirect, flash
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

from app.db.models import Team as TeamModel
from app.db.models import TeamMember, TeamRoles
from app.db.models import User as UserModel
from app.db.models.team_member import TeamMember as TeamMemberModel
from app.domain.accounts.dependencies import provide_users_service
from app.domain.accounts.guards import requires_active_user
from app.domain.accounts.services import UserService
from app.domain.teams.guards import requires_team_admin, requires_team_membership, requires_team_ownership
from app.domain.teams.schemas import (
    CurrentTeam,
    Team,
    TeamCreate,
    TeamDetail,
    TeamDetailPage,
    TeamInvitationItem,
    TeamListItem,
    TeamListPage,
    TeamPageMember,
    TeamPermissions,
    TeamTag,
    TeamUpdate,
)
from app.domain.teams.services import TeamInvitationService, TeamService
from app.lib.schema import NoProps

if TYPE_CHECKING:
    from advanced_alchemy.filters import FilterTypes

__all__ = ("TeamController",)


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
        "TeamInvitationService": TeamInvitationService,
        "TeamService": TeamService,
        "TeamUpdate": TeamUpdate,
        "TeamCreate": TeamCreate,
        "UserService": UserService,
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
    ) -> TeamListPage:
        """List teams that your account can access.

        Returns:
            Teams list with user roles and total count.
        """
        if not teams_service.can_view_all(current_user):
            filters.append(
                TeamModel.id.in_(select(TeamMemberModel.team_id).where(TeamMemberModel.user_id == current_user.id)),  # type: ignore[arg-type]
            )
        results, total = await teams_service.list_and_count(*filters)
        teams = []
        for team in results:
            membership = next((m for m in team.members if m.user_id == current_user.id), None)
            user_role = "owner" if membership and membership.is_owner else str(membership.role) if membership else "member"
            teams.append(
                TeamListItem(
                    id=team.id,
                    name=team.name,
                    slug=team.slug,
                    member_count=len(team.members),
                    user_role=user_role,
                    description=team.description,
                    created_at=team.created_at,
                ),
            )
        return TeamListPage(teams=teams, total=total)

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
        return InertiaRedirect(request, request.url_for("teams.show", team_slug=db_obj.slug))

    @get(
        component="team/show",
        name="teams.show",
        operation_id="GetTeam",
        guards=[requires_team_membership],
        path="/teams/{team_slug:str}/",
        dependencies={
            "team_invitations_service": create_service_provider(TeamInvitationService),
            "users_service": Provide(provide_users_service),
        },
    )
    async def get_team(
        self,
        request: Request,
        teams_service: TeamService,
        team_invitations_service: TeamInvitationService,
        users_service: UserService,
        current_user: UserModel,
        team_slug: Annotated[str, Parameter(title="Team Slug", description="The team slug.")],
    ) -> TeamDetailPage:
        """Get details about a team.

        Returns:
            Team details, members list, pending invitations, and user permissions.
        """
        db_obj = await teams_service.get_one(slug=team_slug)
        request.session.update({"currentTeam": CurrentTeam(team_id=db_obj.id, team_name=db_obj.name)})

        membership = next((m for m in db_obj.members if m.user_id == current_user.id), None)
        is_owner = bool(membership and membership.is_owner)
        is_admin = is_owner or bool(membership and membership.role == TeamRoles.ADMIN)

        # Fetch pending invitations for admins
        invitations = await team_invitations_service.get_pending_for_team(db_obj.id) if is_admin else []
        invitee_flags: dict[str, bool] = {}
        if invitations:
            emails = {inv.email for inv in invitations}
            result = await users_service.repository.session.execute(
                select(UserModel.email).where(UserModel.email.in_(emails)),
            )
            existing_emails = {row[0] for row in result}
            invitee_flags = {email: email in existing_emails for email in emails}

        return TeamDetailPage(
            team=TeamDetail(
                id=db_obj.id,
                name=db_obj.name,
                slug=db_obj.slug,
                description=db_obj.description,
                created_at=db_obj.created_at,
                tags=[TeamTag(id=tag.id, slug=tag.slug, name=tag.name) for tag in db_obj.tags],
            ),
            members=[
                TeamPageMember(
                    id=m.id,
                    user_id=m.user_id,
                    email=m.user.email,
                    role="owner" if m.is_owner else str(m.role),
                    name=m.user.name,
                    avatar_url=m.user.avatar_url,
                )
                for m in db_obj.members
            ],
            pending_invitations=[
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

    @get(
        component="team/settings",
        name="teams.settings",
        operation_id="GetTeamSettings",
        guards=[requires_team_admin],
        path="/teams/{team_slug:str}/settings/",
        dependencies={
            "teams_service": create_service_provider(
                TeamService,
                load=[
                    selectinload(TeamModel.tags),
                    selectinload(TeamModel.members).options(joinedload(TeamMember.user, innerjoin=True)),
                ],
            ),
            "team_invitations_service": create_service_provider(TeamInvitationService),
            "users_service": Provide(provide_users_service),
        },
    )
    async def get_team_settings(
        self,
        request: Request,
        teams_service: TeamService,
        team_invitations_service: TeamInvitationService,
        users_service: UserService,
        current_user: UserModel,
        team_slug: Annotated[str, Parameter(title="Team Slug", description="The team slug.")],
    ) -> TeamDetailPage:
        """Get team settings page.

        Returns:
            Team details, members list, pending invitations, and user permissions for management.
        """
        db_obj = await teams_service.get_one(slug=team_slug)
        request.session.update({"currentTeam": CurrentTeam(team_id=db_obj.id, team_name=db_obj.name)})

        membership = next((m for m in db_obj.members if m.user_id == current_user.id), None)
        is_owner = bool(membership and membership.is_owner)
        is_admin = is_owner or bool(membership and membership.role == TeamRoles.ADMIN)

        invitations = await team_invitations_service.get_pending_for_team(db_obj.id)
        invitee_flags: dict[str, bool] = {}
        if invitations:
            emails = {inv.email for inv in invitations}
            result = await users_service.repository.session.execute(
                select(UserModel.email).where(UserModel.email.in_(emails)),
            )
            existing_emails = {row[0] for row in result}
            invitee_flags = {email: email in existing_emails for email in emails}

        return TeamDetailPage(
            team=TeamDetail(
                id=db_obj.id,
                name=db_obj.name,
                slug=db_obj.slug,
                description=db_obj.description,
                tags=[TeamTag(id=tag.id, slug=tag.slug, name=tag.name) for tag in db_obj.tags],
            ),
            members=[
                TeamPageMember(
                    id=m.id,
                    user_id=m.user_id,
                    email=m.user.email,
                    role="owner" if m.is_owner else str(m.role),
                    name=m.user.name,
                    avatar_url=m.user.avatar_url,
                )
                for m in db_obj.members
            ],
            pending_invitations=[
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

    @patch(
        component="team/edit",
        name="teams.edit",
        operation_id="UpdateTeam",
        guards=[requires_team_admin],
        path="/teams/{team_slug:str}/",
    )
    async def update_team(
        self,
        request: Request,
        data: TeamUpdate,
        teams_service: TeamService,
        team_slug: Annotated[str, Parameter(title="Team Slug", description="The team slug.")],
    ) -> Team:
        """Update a team.

        Returns:
            Updated team data.
        """
        db_obj = await teams_service.get_one(slug=team_slug)
        db_obj = await teams_service.update(
            item_id=db_obj.id,
            data=data.to_dict(),
        )
        request.session.update({"currentTeam": CurrentTeam(team_id=db_obj.id, team_name=db_obj.name)})
        return teams_service.to_schema(schema_type=Team, data=db_obj)

    @delete(
        name="teams.remove",
        operation_id="DeleteTeam",
        guards=[requires_team_ownership],
        path="/teams/{team_slug:str}/",
        status_code=303,
    )
    async def delete_team(
        self,
        request: Request,
        teams_service: TeamService,
        team_slug: Annotated[str, Parameter(title="Team Slug", description="The team slug.")],
    ) -> InertiaRedirect:
        """Delete a team.

        Returns:
            Redirect to teams list page.
        """
        request.session.pop("currentTeam", None)
        db_obj = await teams_service.get_one(slug=team_slug)
        db_obj = await teams_service.delete(db_obj.id)
        flash(request, f'Removed team "{db_obj.name}".', category="info")
        return InertiaRedirect(request, request.url_for("teams.list"))

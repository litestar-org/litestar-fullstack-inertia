"""Admin teams controller."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from advanced_alchemy.extensions.litestar.providers import create_service_dependencies
from litestar import Controller, Request, delete, get, patch, post
from litestar.di import Provide
from litestar.params import Dependency, Parameter
from litestar_vite.inertia import InertiaRedirect, flash
from sqlalchemy.orm import joinedload, selectinload

from app.db.models import AuditAction, TeamMember
from app.db.models import Team as TeamModel
from app.db.models import User as UserModel
from app.domain.accounts.guards import requires_superuser
from app.domain.admin.dependencies import provide_audit_service
from app.domain.admin.schemas import (
    AdminTeamDetail,
    AdminTeamDetailPage,
    AdminTeamListItem,
    AdminTeamListPage,
    AdminTeamMemberAdd,
    AdminTeamUpdate,
    TeamMemberInfo,
)
from app.domain.teams.dependencies import provide_team_members_service
from app.domain.teams.services import TeamMemberService, TeamService

if TYPE_CHECKING:
    from advanced_alchemy.filters import FilterTypes

    from app.domain.admin.services import AuditLogService

__all__ = ("AdminTeamController",)


class AdminTeamController(Controller):
    """Admin team management."""

    tags = ["Admin - Teams"]
    path = "/admin/teams"
    guards = [requires_superuser]
    dependencies = create_service_dependencies(
        TeamService,
        key="teams_service",
        load=[selectinload(TeamModel.members).options(joinedload(TeamMember.user, innerjoin=True))],
        filters={
            "id_filter": UUID,
            "search": "name",
            "pagination_type": "limit_offset",
            "pagination_size": 25,
            "created_at": True,
            "updated_at": True,
            "sort_field": "created_at",
            "sort_order": "desc",
        },
    ) | {"audit_service": Provide(provide_audit_service), "team_members_service": Provide(provide_team_members_service)}

    @get(component="admin/teams/list", name="admin.teams.list", operation_id="AdminListTeams", path="/")
    async def list_teams(
        self, teams_service: TeamService, filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> AdminTeamListPage:
        """List all teams for admin management.

        Returns:
            Paginated list of teams.
        """
        results, total = await teams_service.list_and_count(*filters)

        teams = [
            AdminTeamListItem(
                id=t.id,
                name=t.name,
                slug=t.slug,
                description=t.description,
                is_active=t.is_active,
                member_count=len(t.members),
                owner_email=next((m.user.email for m in t.members if m.is_owner), None),
                created_at=t.created_at,
            )
            for t in results
        ]

        return AdminTeamListPage(teams=teams, total=total)

    @get(
        component="admin/teams/detail", name="admin.teams.detail", operation_id="AdminGetTeam", path="/{team_id:uuid}/",
    )
    async def get_team(
        self,
        teams_service: TeamService,
        team_id: Annotated[UUID, Parameter(title="Team ID", description="The team ID.")],
    ) -> AdminTeamDetailPage:
        """Get team details for admin.

        Returns:
            Team details with member list.
        """
        team = await teams_service.get(team_id)

        return AdminTeamDetailPage(
            team=AdminTeamDetail(
                id=team.id,
                name=team.name,
                slug=team.slug,
                description=team.description,
                is_active=team.is_active,
                members=[
                    TeamMemberInfo(
                        id=m.id,
                        user_id=m.user_id,
                        email=m.user.email,
                        name=m.user.name,
                        role=m.role,
                        is_owner=m.is_owner,
                        avatar_url=m.user.avatar_url,
                    )
                    for m in team.members
                ],
                created_at=team.created_at,
                updated_at=team.updated_at,
            ),
        )

    @patch(name="admin.teams.update", operation_id="AdminUpdateTeam", path="/{team_id:uuid}/")
    async def update_team(
        self,
        request: Request,
        teams_service: TeamService,
        audit_service: AuditLogService,
        current_user: UserModel,
        team_id: Annotated[UUID, Parameter(title="Team ID", description="The team ID.")],
        data: AdminTeamUpdate,
    ) -> InertiaRedirect:
        """Update a team.

        Returns:
            Redirect to team detail page.
        """
        db_obj = await teams_service.update(item_id=team_id, data=data.to_dict())
        await audit_service.log_action(
            actor=current_user,
            action=AuditAction.TEAM_UPDATED,
            target_type="team",
            target_id=db_obj.id,
            target_label=db_obj.name,
            details=data.to_dict(),
            ip_address=request.client.host if request.client else None,
        )
        flash(request, f"Updated team {db_obj.name}", category="success")
        return InertiaRedirect(request, request.url_for("admin.teams.detail", team_id=db_obj.id))

    @post(name="admin.teams.members.add", operation_id="AdminAddTeamMember", path="/{team_id:uuid}/members/")
    async def add_member(
        self,
        request: Request,
        teams_service: TeamService,
        team_members_service: TeamMemberService,
        audit_service: AuditLogService,
        current_user: UserModel,
        team_id: Annotated[UUID, Parameter(title="Team ID", description="The team ID.")],
        data: AdminTeamMemberAdd,
    ) -> InertiaRedirect:
        """Add a member to a team.

        Returns:
            Redirect to team detail page.
        """
        team = await teams_service.get(team_id)
        await team_members_service.create({
            "team_id": team_id,
            "user_id": data.user_id,
            "role": data.role,
            "is_owner": False,
        })

        await audit_service.log_action(
            actor=current_user,
            action=AuditAction.TEAM_MEMBER_ADDED,
            target_type="team",
            target_id=team_id,
            target_label=team.name,
            details={"user_id": str(data.user_id), "role": str(data.role)},
            ip_address=request.client.host if request.client else None,
        )
        flash(request, f"Added member to team {team.name}", category="success")
        return InertiaRedirect(request, request.url_for("admin.teams.detail", team_id=team_id))

    @delete(
        name="admin.teams.members.remove",
        operation_id="AdminRemoveTeamMember",
        path="/{team_id:uuid}/members/{member_id:uuid}/",
        status_code=303,
    )
    async def remove_member(
        self,
        request: Request,
        teams_service: TeamService,
        team_members_service: TeamMemberService,
        audit_service: AuditLogService,
        current_user: UserModel,
        team_id: Annotated[UUID, Parameter(title="Team ID", description="The team ID.")],
        member_id: Annotated[UUID, Parameter(title="Member ID", description="The team member ID.")],
    ) -> InertiaRedirect:
        """Remove a member from a team.

        Returns:
            Redirect to team detail page.
        """
        team = await teams_service.get(team_id)
        member = await team_members_service.get(member_id)

        await team_members_service.delete(member_id)

        await audit_service.log_action(
            actor=current_user,
            action=AuditAction.TEAM_MEMBER_REMOVED,
            target_type="team",
            target_id=team_id,
            target_label=team.name,
            details={"user_id": str(member.user_id)},
            ip_address=request.client.host if request.client else None,
        )
        flash(request, f"Removed member from team {team.name}", category="warning")
        return InertiaRedirect(request, request.url_for("admin.teams.detail", team_id=team_id))

    @delete(name="admin.teams.delete", operation_id="AdminDeleteTeam", path="/{team_id:uuid}/", status_code=303)
    async def delete_team(
        self,
        request: Request,
        teams_service: TeamService,
        audit_service: AuditLogService,
        current_user: UserModel,
        team_id: Annotated[UUID, Parameter(title="Team ID", description="The team ID.")],
    ) -> InertiaRedirect:
        """Delete a team.

        Returns:
            Redirect to teams list.
        """
        db_obj = await teams_service.get(team_id)
        name = db_obj.name
        await teams_service.delete(team_id)

        await audit_service.log_action(
            actor=current_user,
            action=AuditAction.TEAM_DELETED,
            target_type="team",
            target_id=team_id,
            target_label=name,
            ip_address=request.client.host if request.client else None,
        )
        flash(request, f"Deleted team {name}", category="warning")
        return InertiaRedirect(request, request.url_for("admin.teams.list"))

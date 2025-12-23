"""Admin users controller."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from advanced_alchemy.extensions.litestar.providers import create_service_dependencies
from litestar import Controller, Request, delete, get, patch, post
from litestar.di import Provide
from litestar.params import Dependency, Parameter
from litestar_vite.inertia import InertiaRedirect, flash
from sqlalchemy.orm import joinedload, selectinload, undefer_group

from app.db.models import AuditAction, Role, Team, TeamMember, UserRole
from app.db.models import User as UserModel
from app.domain.accounts.dependencies import provide_roles_service, provide_user_roles_service
from app.domain.accounts.guards import requires_superuser
from app.domain.accounts.services import RoleService, UserRoleService, UserService
from app.domain.admin.dependencies import provide_audit_service
from app.domain.admin.schemas import (
    AdminUserCreate,
    AdminUserCreatePage,
    AdminUserDetail,
    AdminUserDetailPage,
    AdminUserListItem,
    AdminUserListPage,
    AdminUserRoleAssign,
    AdminUserUpdate,
    RoleOption,
    UserRoleInfo,
    UserTeamInfo,
)
from app.domain.admin.services import AuditLogService

if TYPE_CHECKING:
    from advanced_alchemy.filters import FilterTypes

__all__ = ("AdminUserController",)


class AdminUserController(Controller):
    """Admin user management."""

    tags = ["Admin - Users"]
    path = "/admin/users"
    guards = [requires_superuser]
    dependencies = create_service_dependencies(
        UserService,
        key="users_service",
        load=[
            selectinload(UserModel.roles).options(joinedload(UserRole.role, innerjoin=True)),
            selectinload(UserModel.teams).options(
                joinedload(TeamMember.team, innerjoin=True),
            ),
        ],
        filters={
            "id_filter": UUID,
            "search": "name,email",
            "pagination_type": "limit_offset",
            "pagination_size": 25,
            "created_at": True,
            "updated_at": True,
            "sort_field": "created_at",
            "sort_order": "desc",
        },
    ) | {
        "roles_service": Provide(provide_roles_service),
        "audit_service": Provide(provide_audit_service),
        "user_roles_service": Provide(provide_user_roles_service),
    }

    @get(
        component="admin/users/list",
        name="admin.users.list",
        operation_id="AdminListUsers",
        path="/",
    )
    async def list_users(
        self,
        users_service: UserService,
        roles_service: RoleService,
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> AdminUserListPage:
        """List all users for admin management.

        Returns:
            Paginated list of users with role information.
        """
        results, total = await users_service.list_and_count(*filters)
        all_roles = await roles_service.list()

        users = [
            AdminUserListItem(
                id=u.id,
                email=u.email,
                name=u.name,
                is_active=u.is_active,
                is_superuser=u.is_superuser,
                is_verified=u.is_verified,
                is_two_factor_enabled=u.is_two_factor_enabled,
                role_names=[r.role_name for r in u.roles],
                team_count=len(u.teams),
                created_at=u.created_at,
                avatar_url=u.avatar_url,
            )
            for u in results
        ]

        return AdminUserListPage(
            users=users,
            total=total,
            roles=[RoleOption(id=r.id, slug=r.slug, name=r.name) for r in all_roles],
        )

    @get(
        component="admin/users/create",
        name="admin.users.create",
        operation_id="AdminCreateUserPage",
        path="/create/",
    )
    async def create_user_page(
        self,
        roles_service: RoleService,
    ) -> AdminUserCreatePage:
        """Show user creation form.

        Returns:
            Page with available roles for assignment.
        """
        all_roles = await roles_service.list()
        return AdminUserCreatePage(
            available_roles=[RoleOption(id=r.id, slug=r.slug, name=r.name) for r in all_roles],
        )

    @post(
        name="admin.users.store",
        operation_id="AdminCreateUser",
        path="/",
    )
    async def create_user(
        self,
        request: Request,
        users_service: UserService,
        audit_service: AuditLogService,
        current_user: UserModel,
        data: AdminUserCreate,
    ) -> InertiaRedirect:
        """Create a new user.

        Returns:
            Redirect to user detail page.
        """
        db_obj = await users_service.create(data.to_dict())
        await audit_service.log_action(
            actor=current_user,
            action=AuditAction.USER_CREATED,
            target_type="user",
            target_id=db_obj.id,
            target_label=db_obj.email,
            ip_address=request.client.host if request.client else None,
        )
        flash(request, f"Created user {db_obj.email}", category="success")
        return InertiaRedirect(request, request.url_for("admin.users.detail", user_id=db_obj.id))

    @get(
        component="admin/users/detail",
        name="admin.users.detail",
        operation_id="AdminGetUser",
        path="/{user_id:uuid}/",
    )
    async def get_user(
        self,
        users_service: UserService,
        roles_service: RoleService,
        user_id: Annotated[UUID, Parameter(title="User ID", description="The user ID.")],
    ) -> AdminUserDetailPage:
        """Get user details for admin.

        Returns:
            User details with roles and team memberships.
        """
        # Load user with security_sensitive group to access has_password,
        # plus roles and teams relationships
        user = await users_service.get(
            user_id,
            load=[
                undefer_group("security_sensitive"),
                selectinload(UserModel.roles).options(joinedload(UserRole.role, innerjoin=True)),
                selectinload(UserModel.teams).options(joinedload(TeamMember.team, innerjoin=True)),
            ],
        )
        all_roles = await roles_service.list()

        return AdminUserDetailPage(
            user=AdminUserDetail(
                id=user.id,
                email=user.email,
                name=user.name,
                is_active=user.is_active,
                is_superuser=user.is_superuser,
                is_verified=user.is_verified,
                is_two_factor_enabled=user.is_two_factor_enabled,
                has_password=user.has_password,
                roles=[
                    UserRoleInfo(
                        id=r.id,
                        role_id=r.role_id,
                        role_slug=r.role_slug,
                        role_name=r.role_name,
                        assigned_at=r.assigned_at,
                    )
                    for r in user.roles
                ],
                teams=[
                    UserTeamInfo(
                        team_id=t.team_id,
                        team_name=t.team.name,
                        team_slug=t.team.slug,
                        role=t.role,
                        is_owner=t.is_owner,
                    )
                    for t in user.teams
                ],
                created_at=user.created_at,
                updated_at=user.updated_at,
                avatar_url=user.avatar_url,
            ),
            available_roles=[RoleOption(id=r.id, slug=r.slug, name=r.name) for r in all_roles],
        )

    @patch(
        name="admin.users.update",
        operation_id="AdminUpdateUser",
        path="/{user_id:uuid}/",
    )
    async def update_user(
        self,
        request: Request,
        users_service: UserService,
        audit_service: AuditLogService,
        current_user: UserModel,
        user_id: Annotated[UUID, Parameter(title="User ID", description="The user ID.")],
        data: AdminUserUpdate,
    ) -> InertiaRedirect:
        """Update a user.

        Returns:
            Redirect to user detail page.
        """
        db_obj = await users_service.update(item_id=user_id, data=data.to_dict())
        await audit_service.log_action(
            actor=current_user,
            action=AuditAction.USER_UPDATED,
            target_type="user",
            target_id=db_obj.id,
            target_label=db_obj.email,
            details=data.to_dict(),
            ip_address=request.client.host if request.client else None,
        )
        flash(request, f"Updated user {db_obj.email}", category="success")
        return InertiaRedirect(request, request.url_for("admin.users.detail", user_id=db_obj.id))

    @post(
        name="admin.users.lock",
        operation_id="AdminLockUser",
        path="/{user_id:uuid}/lock/",
    )
    async def lock_user(
        self,
        request: Request,
        users_service: UserService,
        audit_service: AuditLogService,
        current_user: UserModel,
        user_id: Annotated[UUID, Parameter(title="User ID", description="The user ID.")],
    ) -> InertiaRedirect:
        """Lock (deactivate) a user account.

        Returns:
            Redirect to user detail page.
        """
        db_obj = await users_service.update(item_id=user_id, data={"is_active": False})
        await audit_service.log_action(
            actor=current_user,
            action=AuditAction.USER_LOCKED,
            target_type="user",
            target_id=db_obj.id,
            target_label=db_obj.email,
            ip_address=request.client.host if request.client else None,
        )
        flash(request, f"Locked user {db_obj.email}", category="warning")
        return InertiaRedirect(request, request.url_for("admin.users.detail", user_id=db_obj.id))

    @post(
        name="admin.users.unlock",
        operation_id="AdminUnlockUser",
        path="/{user_id:uuid}/unlock/",
    )
    async def unlock_user(
        self,
        request: Request,
        users_service: UserService,
        audit_service: AuditLogService,
        current_user: UserModel,
        user_id: Annotated[UUID, Parameter(title="User ID", description="The user ID.")],
    ) -> InertiaRedirect:
        """Unlock (activate) a user account.

        Returns:
            Redirect to user detail page.
        """
        db_obj = await users_service.update(item_id=user_id, data={"is_active": True})
        await audit_service.log_action(
            actor=current_user,
            action=AuditAction.USER_UNLOCKED,
            target_type="user",
            target_id=db_obj.id,
            target_label=db_obj.email,
            ip_address=request.client.host if request.client else None,
        )
        flash(request, f"Unlocked user {db_obj.email}", category="success")
        return InertiaRedirect(request, request.url_for("admin.users.detail", user_id=db_obj.id))

    @post(
        name="admin.users.verify",
        operation_id="AdminVerifyUser",
        path="/{user_id:uuid}/verify/",
    )
    async def verify_user(
        self,
        request: Request,
        users_service: UserService,
        audit_service: AuditLogService,
        current_user: UserModel,
        user_id: Annotated[UUID, Parameter(title="User ID", description="The user ID.")],
    ) -> InertiaRedirect:
        """Manually verify a user's email.

        Returns:
            Redirect to user detail page.
        """
        db_obj = await users_service.update(item_id=user_id, data={"is_verified": True})
        await audit_service.log_action(
            actor=current_user,
            action=AuditAction.USER_VERIFIED,
            target_type="user",
            target_id=db_obj.id,
            target_label=db_obj.email,
            ip_address=request.client.host if request.client else None,
        )
        flash(request, f"Verified user {db_obj.email}", category="success")
        return InertiaRedirect(request, request.url_for("admin.users.detail", user_id=db_obj.id))

    @post(
        name="admin.users.unverify",
        operation_id="AdminUnverifyUser",
        path="/{user_id:uuid}/unverify/",
    )
    async def unverify_user(
        self,
        request: Request,
        users_service: UserService,
        audit_service: AuditLogService,
        current_user: UserModel,
        user_id: Annotated[UUID, Parameter(title="User ID", description="The user ID.")],
    ) -> InertiaRedirect:
        """Remove verification from a user.

        Returns:
            Redirect to user detail page.
        """
        db_obj = await users_service.update(item_id=user_id, data={"is_verified": False})
        await audit_service.log_action(
            actor=current_user,
            action=AuditAction.USER_UNVERIFIED,
            target_type="user",
            target_id=db_obj.id,
            target_label=db_obj.email,
            ip_address=request.client.host if request.client else None,
        )
        flash(request, f"Unverified user {db_obj.email}", category="warning")
        return InertiaRedirect(request, request.url_for("admin.users.detail", user_id=db_obj.id))

    @post(
        name="admin.users.roles.assign",
        operation_id="AdminAssignRole",
        path="/{user_id:uuid}/roles/",
    )
    async def assign_role(
        self,
        request: Request,
        users_service: UserService,
        user_roles_service: UserRoleService,
        roles_service: RoleService,
        audit_service: AuditLogService,
        current_user: UserModel,
        user_id: Annotated[UUID, Parameter(title="User ID", description="The user ID.")],
        data: AdminUserRoleAssign,
    ) -> InertiaRedirect:
        """Assign a role to a user.

        Returns:
            Redirect to user detail page.
        """
        user = await users_service.get(user_id)
        role = await roles_service.get(data.role_id)

        await user_roles_service.create({"user_id": user_id, "role_id": data.role_id})

        await audit_service.log_action(
            actor=current_user,
            action=AuditAction.USER_ROLE_ASSIGNED,
            target_type="user",
            target_id=user_id,
            target_label=user.email,
            details={"role_id": str(data.role_id), "role_name": role.name},
            ip_address=request.client.host if request.client else None,
        )
        flash(request, f"Assigned role '{role.name}' to {user.email}", category="success")
        return InertiaRedirect(request, request.url_for("admin.users.detail", user_id=user_id))

    @delete(
        name="admin.users.roles.revoke",
        operation_id="AdminRevokeRole",
        path="/{user_id:uuid}/roles/{user_role_id:uuid}/",
        status_code=303,
    )
    async def revoke_role(
        self,
        request: Request,
        users_service: UserService,
        user_roles_service: UserRoleService,
        audit_service: AuditLogService,
        current_user: UserModel,
        user_id: Annotated[UUID, Parameter(title="User ID", description="The user ID.")],
        user_role_id: Annotated[UUID, Parameter(title="User Role ID", description="The user-role assignment ID.")],
    ) -> InertiaRedirect:
        """Revoke a role from a user.

        Returns:
            Redirect to user detail page.
        """
        user = await users_service.get(user_id)
        user_role = await user_roles_service.get(user_role_id)

        await user_roles_service.delete(user_role_id)

        await audit_service.log_action(
            actor=current_user,
            action=AuditAction.USER_ROLE_REVOKED,
            target_type="user",
            target_id=user_id,
            target_label=user.email,
            details={"role_name": user_role.role_name},
            ip_address=request.client.host if request.client else None,
        )
        flash(request, f"Revoked role '{user_role.role_name}' from {user.email}", category="warning")
        return InertiaRedirect(request, request.url_for("admin.users.detail", user_id=user_id))

    @delete(
        name="admin.users.delete",
        operation_id="AdminDeleteUser",
        path="/{user_id:uuid}/",
        status_code=303,
    )
    async def delete_user(
        self,
        request: Request,
        users_service: UserService,
        audit_service: AuditLogService,
        current_user: UserModel,
        user_id: Annotated[UUID, Parameter(title="User ID", description="The user ID.")],
    ) -> InertiaRedirect:
        """Delete a user.

        Returns:
            Redirect to users list.
        """
        db_obj = await users_service.get(user_id)
        email = db_obj.email
        await users_service.delete(user_id)

        await audit_service.log_action(
            actor=current_user,
            action=AuditAction.USER_DELETED,
            target_type="user",
            target_id=user_id,
            target_label=email,
            ip_address=request.client.host if request.client else None,
        )
        flash(request, f"Deleted user {email}", category="warning")
        return InertiaRedirect(request, request.url_for("admin.users.list"))

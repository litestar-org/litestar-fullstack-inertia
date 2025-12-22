"""Role management controllers."""

from __future__ import annotations

from litestar import Controller, post
from litestar.di import Provide
from litestar.params import Parameter
from litestar.repository.exceptions import ConflictError

from app.domain.accounts.dependencies import provide_roles_service, provide_user_roles_service, provide_users_service
from app.domain.accounts.guards import requires_superuser
from app.domain.accounts.schemas import UserRoleAdd, UserRoleRevoke
from app.domain.accounts.services import RoleService, UserRoleService, UserService
from app.lib.schema import Message

__all__ = ("RoleController", "UserRoleController")


class RoleController(Controller):
    """Handles the adding and removing of new Roles."""

    tags = ["Roles"]
    guards = [requires_superuser]
    dependencies = {"roles_service": Provide(provide_roles_service)}
    signature_namespace = {"RoleService": RoleService}


class UserRoleController(Controller):
    """Handles the adding and removing of User Role records."""

    tags = ["User Account Roles"]
    guards = [requires_superuser]
    dependencies = {
        "users_service": Provide(provide_users_service),
        "roles_service": Provide(provide_roles_service),
        "user_roles_service": Provide(provide_user_roles_service),
    }
    signature_namespace = {
        "UserService": UserService,
        "RoleService": RoleService,
        "UserRoleService": UserRoleService,
        "UserRoleAdd": UserRoleAdd,
        "UserRoleRevoke": UserRoleRevoke,
    }

    @post(operation_id="AssignUserRole", name="users:assign-role", path="/api/roles/{role_slug:str}/assign")
    async def assign_role(
        self,
        roles_service: RoleService,
        users_service: UserService,
        user_roles_service: UserRoleService,
        data: UserRoleAdd,
        role_slug: str = Parameter(title="Role Slug", description="The role to grant."),
    ) -> Message:
        """Assign a role to a user.

        Returns:
            Success message indicating role assignment status.
        """
        role_id = (await roles_service.get_one(slug=role_slug)).id
        user_obj = await users_service.get_one(email=data.user_name)
        obj, created = await user_roles_service.get_or_upsert(role_id=role_id, user_id=user_obj.id, upsert=False)
        if created:
            return Message(message=f"Successfully assigned the '{obj.role_slug}' role to {obj.user_email}.")
        return Message(message=f"User {obj.user_email} already has the '{obj.role_slug}' role.")

    @post(
        operation_id="RevokeUserRole",
        name="users:revoke-role",
        summary="Remove Role",
        description="Removes an assigned role from a user.",
        path="/api/roles/{role_slug:str}/revoke",
    )
    async def revoke_role(
        self,
        users_service: UserService,
        user_roles_service: UserRoleService,
        data: UserRoleRevoke,
        role_slug: str = Parameter(title="Role Slug", description="The role to revoke."),
    ) -> Message:
        """Revoke a role from a user.

        Returns:
            Success message confirming role removal.

        Raises:
            ConflictError: If the user did not have the role assigned.
        """
        user_obj = await users_service.get_one(email=data.user_name)
        removed_role: bool = False
        for user_role in user_obj.roles:
            if user_role.role_slug == role_slug:
                _ = await user_roles_service.delete(user_role.id)
                removed_role = True
        if not removed_role:
            msg = "User did not have role assigned."
            raise ConflictError(msg)
        return Message(message=f"Removed the '{role_slug}' role from User {user_obj.email}.")

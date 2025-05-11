"""User Account Controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any
from uuid import UUID

from advanced_alchemy.extensions.litestar.providers import create_filter_dependencies, create_service_provider
from advanced_alchemy.service import schema_dump
from advanced_alchemy.utils.text import slugify
from litestar import Controller, Request, Response, delete, get, patch, post
from litestar.di import Provide
from litestar.params import Dependency, Parameter
from litestar.plugins.flash import flash
from litestar.repository.exceptions import ConflictError
from litestar_vite.inertia import InertiaExternalRedirect, InertiaRedirect, share
from sqlalchemy.orm import joinedload, selectinload

from app.config import github_oauth2_client, google_oauth2_client
from app.db import models as m
from app.domain.accounts import deps, guards, schemas, services
from app.lib.oauth import AccessTokenState
from app.lib.schema import Message

if TYPE_CHECKING:
    from advanced_alchemy.filters import FilterTypes
    from advanced_alchemy.service import OffsetPagination


class AccessController(Controller):
    """User login and registration."""

    include_in_schema = False
    dependencies = {
        "users_service": Provide(deps.provide_users_service),
        "roles_service": Provide(
            create_service_provider(
                services.RoleService,
                load=[selectinload(m.Role.users).options(joinedload(m.UserRole.user, innerjoin=True))],
            ),
        ),
    }
    exclude_from_auth = True

    @get(component="auth/login", name="login", path="/login/")
    async def show_login(self, request: Request) -> Response | dict:
        """Show the user login page.

        Args:
            request: The request object.

        Returns:
            The response object.
        """
        if request.session.get("user_id", False):
            flash(request, "Your account is already authenticated.", category="info")
            return InertiaRedirect(request, request.url_for("dashboard"))
        return {}

    @post(component="auth/login", name="login.check", path="/login/")
    async def login(
        self,
        request: Request,
        users_service: services.UserService,
        data: schemas.AccountLogin,
    ) -> Response:
        """Authenticate a user.

        Args:
            request: The request object.
            users_service: The users service.
            data: The login data.

        Returns:
            The response object.
        """
        user = await users_service.authenticate(data.username, data.password)
        request.set_session({"user_id": user.email})
        flash(request, "Your account was successfully authenticated.", category="info")
        request.logger.info("Redirecting to %s ", request.url_for("dashboard"))
        return InertiaRedirect(request, request.url_for("dashboard"))

    @post(name="logout", path="/logout/", exclude_from_auth=False)
    async def logout(self, request: Request) -> Response:
        """Account Logout

        Args:
            request: The request object.

        Returns:
            The response object.
        """
        flash(request, "You have been logged out.", category="info")
        request.clear_session()
        return InertiaRedirect(request, request.url_for("login"))


class RegistrationController(Controller):
    include_in_schema = False
    dependencies = {
        "users_service": Provide(deps.provide_users_service),
        "roles_service": Provide(
            create_service_provider(services.RoleService),
        ),
        "oauth_account_service": Provide(
            create_service_provider(
                services.UserOAuthAccountService,
                load=[m.UserOAuthAccount.user],
            ),
        ),
    }
    exclude_from_auth = True

    @get(component="auth/register", name="register", path="/register/")
    async def show_signup(self, request: Request) -> Response | dict:
        """Show the user login page.

        Args:
            request: The request object.

        Returns:
            The response object.
        """
        if request.session.get("user_id", False):
            flash(request, "Your account is already authenticated.  Welcome back!", category="info")
            return InertiaRedirect(request, request.url_for("dashboard"))
        return {}

    @post(component="auth/register", name="register.add", path="/register/")
    async def signup(
        self,
        request: Request,
        users_service: services.UserService,
        roles_service: services.RoleService,
        data: schemas.AccountRegister,
    ) -> Response:
        """User Signup.

        Args:
            request: The request object.
            users_service: The users service.
            roles_service: The roles service.
            data: The register data.

        Returns:
            The response object.
        """
        user_data = schema_dump(data)
        role_obj = await roles_service.get_one_or_none(slug=slugify(users_service.default_role))
        if role_obj is not None:
            user_data.update({"role_id": role_obj.id})
        user = await users_service.create(user_data)
        request.set_session({"user_id": user.email})
        request.app.emit(event_id="user_created", user_id=user.id)
        flash(request, "Account created successfully.  Welcome!", category="info")
        return InertiaRedirect(request, request.url_for("dashboard"))

    @post(name="github.register", path="/register/github/")
    async def github_signup(self, request: Request) -> InertiaExternalRedirect:
        """Redirect to the Github Login page.

        Args:
            request: The request object.

        Returns:
            The response object.
        """
        redirect_to = await github_oauth2_client.get_authorization_url(redirect_uri=request.url_for("github.complete"))
        return InertiaExternalRedirect(request, redirect_to=redirect_to)

    @get(
        name="github.complete",
        path="/o/github/complete/",
        dependencies={"access_token_state": Provide(guards.github_oauth_callback)},
        signature_namespace={"AccessTokenState": AccessTokenState},
    )
    async def github_complete(
        self,
        request: Request,
        access_token_state: AccessTokenState,
        roles_service: services.RoleService,
        users_service: services.UserService,
    ) -> InertiaRedirect:
        """Redirect to the Github Login page.

        Args:
            request: The request object.
            access_token_state: The access token state.
            roles_service: The roles service.
            users_service: The users service.

        Returns:
            The response object.
        """
        token, _state = access_token_state
        account_id, email = await github_oauth2_client.get_id_email(token=token["access_token"])
        data: dict[str, Any] = {"email": email, "account_id": account_id}
        role_obj = await roles_service.get_one_or_none(slug=slugify(users_service.default_role))
        if role_obj is not None:
            data.update({"role_id": role_obj.id})
        user, created = await users_service.get_or_upsert(
            match_fields=["email"],
            email=email,
            is_verified=True,
            is_active=True,
        )
        request.set_session({"user_id": user.email})
        if created:
            request.logger.info("created a new user", id=user.id)
            flash(request, "Welcome to fullstack.  Your account is ready", category="info")
        share(
            request,
            "auth",
            {"isAuthenticated": True, "user": users_service.to_schema(user, schema_type=schemas.User)},
        )
        return InertiaRedirect(request, redirect_to=request.url_for("dashboard"))

    @post(name="google.register", path="/register/google/")
    async def google_signup(self, request: Request) -> InertiaExternalRedirect:
        """Redirect to the Github Login page.

        Args:
            request: The request object.

        Returns:
            The response object.
        """
        redirect_to = await google_oauth2_client.get_authorization_url(redirect_uri=request.url_for("google.complete"))
        return InertiaExternalRedirect(request, redirect_to=redirect_to)

    @get(
        name="google.complete",
        path="/o/google/complete/",
        dependencies={"access_token_state": Provide(guards.google_oauth_callback)},
        signature_namespace={"AccessTokenState": AccessTokenState},
    )
    async def google_complete(
        self,
        request: Request,
        access_token_state: AccessTokenState,
        users_service: services.UserService,
    ) -> InertiaRedirect:
        """Redirect to the Github Login page.

        Args:
            request: The request object.
            access_token_state: The access token state.
            users_service: The users service.

        Returns:
            The response object.
        """
        token, _state = access_token_state
        auth_id, email = await google_oauth2_client.get_id_email(token=token["access_token"])

        user, created = await users_service.get_or_upsert(
            match_fields=["email"],
            email=email,
            is_verified=True,
            is_active=True,
        )
        request.set_session({"user_id": user.email})
        request.logger.info("google auth request", id=auth_id, email=email)
        if created:
            request.logger.info("created a new user", id=user.id)
            flash(request, "Welcome to fullstack.  Your account is ready", category="info")
        share(
            request,
            "auth",
            {"isAuthenticated": True, "user": users_service.to_schema(user, schema_type=schemas.User)},
        )
        return InertiaRedirect(request, redirect_to=request.url_for("dashboard"))


class ProfileController(Controller):
    include_in_schema = False
    dependencies = {"users_service": Provide(deps.provide_users_service)}
    guards = [guards.requires_active_user]

    @get(component="profile/edit", name="profile.show", path="/profile/")
    async def profile(self, current_user: m.User, users_service: services.UserService) -> schemas.User:
        """User Profile.

        Args:
            current_user: The current user.
            users_service: The users service.

        Returns:
            The response object.
        """
        return users_service.to_schema(current_user, schema_type=schemas.User)

    @patch(component="profile/edit", name="profile.update", path="/profile/")
    async def update_profile(
        self,
        current_user: m.User,
        data: schemas.ProfileUpdate,
        users_service: services.UserService,
    ) -> schemas.User:
        """User Profile.

        Args:
            current_user: The current user.
            data: The profile update data.
            users_service: The users service.

        Returns:
            The response object.
        """
        db_obj = await users_service.update(data, item_id=current_user.id)
        return users_service.to_schema(db_obj, schema_type=schemas.User)

    @patch(component="profile/edit", name="password.update", path="/profile/password-update/")
    async def update_password(
        self,
        current_user: m.User,
        data: schemas.PasswordUpdate,
        users_service: services.UserService,
    ) -> Message:
        """Update user password.

        Args:
            current_user: The current user.
            data: The password update data.
            users_service: The users service.

        Returns:
            The response object.
        """
        await users_service.update_password(data.to_dict(), db_obj=current_user)
        return Message(message="Your password was successfully modified.")

    @delete(name="account.remove", path="/profile/", status_code=303)
    async def remove_account(
        self,
        request: Request,
        current_user: m.User,
        users_service: services.UserService,
    ) -> InertiaRedirect:
        """Remove your account.

        Args:
            request: The request object.
            current_user: The current user.
            users_service: The users service.

        Returns:
            The response object.
        """
        request.session.clear()
        _ = await users_service.delete(current_user.id)
        flash(request, "Your account has been removed from the system.", category="info")
        return InertiaRedirect(request, request.url_for("landing"))


class RoleController(Controller):
    """Handles the adding and removing of new Roles."""

    tags = ["Roles"]
    guards = [guards.requires_superuser]
    dependencies = {
        "roles_service": Provide(
            create_service_provider(
                services.RoleService,
                load=[selectinload(m.Role.users).options(joinedload(m.UserRole.user, innerjoin=True))],
            ),
        ),
    }


class UserRoleController(Controller):
    """Handles the adding and removing of User Role records."""

    tags = ["User Account Roles"]
    guards = [guards.requires_superuser]
    dependencies = {
        "users_service": Provide(deps.provide_users_service),
        "roles_service": Provide(
            create_service_provider(services.RoleService),
        ),
        "user_roles_service": Provide(
            create_service_provider(
                services.UserRoleService,
                load=[m.UserRole.user],
            ),
        ),
    }

    @post(
        operation_id="AssignUserRole",
        name="users:assign-role",
        path="/api/roles/{role_slug:str}/assign",
    )
    async def assign_role(
        self,
        roles_service: services.RoleService,
        users_service: services.UserService,
        user_roles_service: services.UserRoleService,
        data: schemas.UserRoleAdd,
        role_slug: str = Parameter(
            title="Role Slug",
            description="The role to grant.",
        ),
    ) -> Message:
        """Create a new migration role.

        Args:
            roles_service: The roles service.
            users_service: The users service.
            user_roles_service: The user roles service.
            data: The user role add data.
            role_slug: The role slug.

        Returns:
            The response object.
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
        path="/api/roles/{role_slug:str}/revoke",
    )
    async def revoke_role(
        self,
        users_service: services.UserService,
        user_roles_service: services.UserRoleService,
        data: schemas.UserRoleRevoke,
        role_slug: str = Parameter(
            title="Role Slug",
            description="The role to revoke.",
        ),
    ) -> Message:
        """Delete a role from the system.

        Args:
            users_service: The users service.
            user_roles_service: The user roles service.
            data: The user role revoke data.
            role_slug: The role slug.

        Raises:
            ConflictError: If the user does not have the role assigned.

        Returns:
            The response object.
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


class UserController(Controller):
    """User Account Controller."""

    tags = ["User Accounts"]
    guards = [guards.requires_superuser]
    dependencies = {
        "users_service": Provide(deps.provide_users_service),
    } | create_filter_dependencies(
        {
            "id_filter": UUID,
            "search": "email,name",
            "pagination_type": "limit_offset",
            "pagination_size": 20,
            "created_at": True,
            "updated_at": True,
            "sort_field": "name",
            "sort_order": "asc",
        },
    )

    @get(
        operation_id="ListUsers",
        name="users:list",
        path="/api/users",
        cache=60,
    )
    async def list_users(
        self,
        users_service: services.UserService,
        filters: list[FilterTypes] = Dependency(skip_validation=True),
    ) -> OffsetPagination[schemas.User]:
        """List users.

        Args:
            users_service: The users service.
            filters: The filters.

        Returns:
            The response object.
        """
        results, total = await users_service.list_and_count(*filters)
        return users_service.to_schema(data=results, total=total, schema_type=schemas.User, filters=filters)

    @get(
        operation_id="GetUser",
        name="users:get",
        path="/api/users/{user_id:uuid}",
        summary="Retrieve the details of a user.",
    )
    async def get_user(
        self,
        users_service: services.UserService,
        user_id: UUID = Parameter(title="User ID", description="The user to retrieve."),
    ) -> schemas.User:
        """Get a user.

        Args:
            users_service: The users service.
            user_id: The user ID.

        Returns:
            The response object.
        """
        db_obj = await users_service.get(user_id)
        return users_service.to_schema(db_obj, schema_type=schemas.User)

    @post(
        operation_id="CreateUser",
        name="users:create",
        summary="Create a new user.",
        cache_control=None,
        description="A user who can login and use the system.",
        path="/api/users",
    )
    async def create_user(
        self,
        users_service: services.UserService,
        data: schemas.UserCreate,
    ) -> schemas.User:
        """Create a new user.

        Args:
            users_service: The users service.
            data: The user create data.

        Returns:
            The response object.
        """
        db_obj = await users_service.create(data.to_dict())
        return users_service.to_schema(db_obj, schema_type=schemas.User)

    @patch(
        operation_id="UpdateUser",
        name="users:update",
        path="/api/users/{user_id:uuid}",
    )
    async def update_user(
        self,
        data: schemas.UserUpdate,
        users_service: services.UserService,
        user_id: UUID = Parameter(
            title="User ID",
            description="The user to update.",
        ),
    ) -> schemas.User:
        """Update a user.

        Args:
            data: The user update data.
            users_service: The users service.
            user_id: The user ID.

        Returns:
            The response object.
        """
        db_obj = await users_service.update(item_id=user_id, data=data)
        return users_service.to_schema(db_obj, schema_type=schemas.User)

    @delete(name="users:delete", path="/api/users/{user_id:uuid}")
    async def delete_user(
        self,
        users_service: services.UserService,
        user_id: Annotated[
            UUID,
            Parameter(
                title="User ID",
                description="The user to delete.",
            ),
        ],
    ) -> None:
        """Delete a user from the system.

        Args:
            users_service: The users service.
            user_id: The user ID.
        """
        _ = await users_service.delete(user_id)

"""User Account Controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any

from advanced_alchemy.utils.text import slugify
from litestar import Controller, Request, Response, delete, get, patch, post
from litestar.di import Provide
from litestar.params import Dependency, Parameter
from litestar.plugins.flash import flash
from litestar.repository.exceptions import ConflictError
from litestar_vite.inertia import InertiaExternalRedirect, InertiaRedirect, share

from app.config import github_oauth2_client, google_oauth2_client
from app.domain.accounts import schemas
from app.domain.accounts.dependencies import (
    provide_roles_service,
    provide_user_oauth_account_service,
    provide_user_roles_service,
    provide_users_service,
)
from app.domain.accounts.guards import (
    github_oauth_callback,
    google_oauth_callback,
    requires_active_user,
    requires_superuser,
)
from app.domain.accounts.services import RoleService, UserOAuthAccountService, UserRoleService, UserService
from app.lib.oauth import AccessTokenState
from app.lib.schema import Message

if TYPE_CHECKING:
    from uuid import UUID

    from advanced_alchemy.filters import FilterTypes
    from advanced_alchemy.service import OffsetPagination

    from app.db.models import User as UserModel


class AccessController(Controller):
    """User login and registration."""

    include_in_schema = False
    dependencies = {"users_service": Provide(provide_users_service)}
    signature_namespace = {
        "UserService": UserService,
        "AccountLogin": schemas.AccountLogin,
    }
    cache = False
    exclude_from_auth = True

    @get(component="auth/login", name="login", path="/login/")
    async def show_login(
        self,
        request: Request,
    ) -> Response | dict:
        """Show the user login page."""
        if request.session.get("user_id", False):
            flash(request, "Your account is already authenticated.", category="info")
            return InertiaRedirect(request, request.url_for("dashboard"))
        return {}

    @post(component="auth/login", name="login.check", path="/login/")
    async def login(
        self,
        request: Request[Any, Any, Any],
        users_service: UserService,
        data: schemas.AccountLogin,
    ) -> Response:
        """Authenticate a user."""
        user = await users_service.authenticate(data.username, data.password)
        request.set_session({"user_id": user.email})
        flash(request, "Your account was successfully authenticated.", category="info")
        request.logger.info("Redirecting to %s ", request.url_for("dashboard"))
        return InertiaRedirect(request, request.url_for("dashboard"))

    @post(name="logout", path="/logout/", exclude_from_auth=False)
    async def logout(
        self,
        request: Request,
    ) -> Response:
        """Account Logout"""
        flash(request, "You have been logged out.", category="info")
        request.clear_session()
        return InertiaRedirect(request, request.url_for("login"))


class RegistrationController(Controller):
    include_in_schema = False
    dependencies = {
        "users_service": Provide(provide_users_service),
        "roles_service": Provide(provide_roles_service),
        "oauth_account_service": Provide(provide_user_oauth_account_service),
    }
    signature_namespace = {
        "UserService": UserService,
        "RoleService": RoleService,
        "UserOAuthAccountService": UserOAuthAccountService,
        "AccountRegister": schemas.AccountRegister,
    }
    exclude_from_auth = True

    @get(component="auth/register", name="register", path="/register/")
    async def show_signup(
        self,
        request: Request,
    ) -> Response | dict:
        """Show the user login page."""
        if request.session.get("user_id", False):
            flash(request, "Your account is already authenticated.  Welcome back!", category="info")
            return InertiaRedirect(request, request.url_for("dashboard"))
        return {}

    @post(component="auth/register", name="register.add", path="/register/")
    async def signup(
        self,
        request: Request,
        users_service: UserService,
        roles_service: RoleService,
        data: schemas.AccountRegister,
    ) -> Response:
        """User Signup."""
        user_data = data.to_dict()
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
        """Redirect to the Github Login page."""
        redirect_to = await github_oauth2_client.get_authorization_url(redirect_uri=request.url_for("github.complete"))
        return InertiaExternalRedirect(request, redirect_to=redirect_to)

    @get(
        name="github.complete",
        path="/o/github/complete/",
        dependencies={"access_token_state": Provide(github_oauth_callback)},
        signature_namespace={"AccessTokenState": AccessTokenState},
    )
    async def github_complete(
        self,
        request: Request,
        access_token_state: AccessTokenState,
        roles_service: RoleService,
        oauth_account_service: UserOAuthAccountService,
        users_service: UserService,
    ) -> InertiaRedirect:
        """Redirect to the Github Login page."""
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
    async def google_signup(
        self,
        request: Request,
    ) -> InertiaExternalRedirect:
        """Redirect to the Github Login page."""
        redirect_to = await google_oauth2_client.get_authorization_url(redirect_uri=request.url_for("google.complete"))
        return InertiaExternalRedirect(request, redirect_to=redirect_to)

    @get(
        name="google.complete",
        path="/o/google/complete/",
        dependencies={"access_token_state": Provide(google_oauth_callback)},
        signature_namespace={"AccessTokenState": AccessTokenState},
    )
    async def google_complete(
        self,
        request: Request,
        access_token_state: AccessTokenState,
        users_service: UserService,
    ) -> InertiaRedirect:
        """Redirect to the Github Login page."""
        token, _state = access_token_state
        _id, email = await google_oauth2_client.get_id_email(token=token["access_token"])

        user, created = await users_service.get_or_upsert(
            match_fields=["email"],
            email=email,
            is_verified=True,
            is_active=True,
        )
        request.set_session({"user_id": user.email})
        request.logger.info("google auth request", id=_id, email=email)
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
    dependencies = {"users_service": Provide(provide_users_service)}
    signature_namespace = {
        "UserService": UserService,
        "User": schemas.User,
        "ProfileUpdate": schemas.ProfileUpdate,
        "PasswordUpdate": schemas.PasswordUpdate,
    }
    guards = [requires_active_user]

    @get(component="profile/edit", name="profile.show", path="/profile/")
    async def profile(self, current_user: UserModel, users_service: UserService) -> schemas.User:
        """User Profile."""
        return users_service.to_schema(current_user, schema_type=schemas.User)

    @patch(component="profile/edit", name="profile.update", path="/profile/")
    async def update_profile(
        self,
        current_user: UserModel,
        data: schemas.ProfileUpdate,
        users_service: UserService,
    ) -> schemas.User:
        """User Profile."""
        db_obj = await users_service.update(data, item_id=current_user.id)
        return users_service.to_schema(db_obj, schema_type=schemas.User)

    @patch(component="profile/edit", name="password.update", path="/profile/password-update/")
    async def update_password(
        self,
        current_user: UserModel,
        data: schemas.PasswordUpdate,
        users_service: UserService,
    ) -> Message:
        """Update user password."""
        await users_service.update_password(data.to_dict(), db_obj=current_user)
        return Message(message="Your password was successfully modified.")

    @delete(name="account.remove", path="/profile/", status_code=303)
    async def remove_account(
        self,
        request: Request,
        current_user: UserModel,
        users_service: UserService,
    ) -> InertiaRedirect:
        """Remove your account."""
        request.session.clear()
        _ = await users_service.delete(current_user.id)
        flash(request, "Your account has been removed from the system.", category="info")
        return InertiaRedirect(request, request.url_for("landing"))


class RoleController(Controller):
    """Handles the adding and removing of new Roles."""

    tags = ["Roles"]
    guards = [requires_superuser]
    dependencies = {
        "roles_service": Provide(provide_roles_service),
    }
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
        "UserRoleAdd": schemas.UserRoleAdd,
        "UserRoleRevoke": schemas.UserRoleRevoke,
    }

    @post(
        operation_id="AssignUserRole",
        name="users:assign-role",
        path="/api/roles/{role_slug:str}/assign",
    )
    async def assign_role(
        self,
        roles_service: RoleService,
        users_service: UserService,
        user_roles_service: UserRoleService,
        data: schemas.UserRoleAdd,
        role_slug: str = Parameter(
            title="Role Slug",
            description="The role to grant.",
        ),
    ) -> Message:
        """Create a new migration role."""
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
        data: schemas.UserRoleRevoke,
        role_slug: str = Parameter(
            title="Role Slug",
            description="The role to revoke.",
        ),
    ) -> Message:
        """Delete a role from the system."""
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
    guards = [requires_superuser]
    dependencies = {"users_service": Provide(provide_users_service)}
    signature_namespace = {
        "UserService": UserService,
        "User": schemas.User,
        "UserUpdate": schemas.UserUpdate,
        "UserCreate": schemas.UserCreate,
    }
    dto = None
    return_dto = None

    @get(
        operation_id="ListUsers",
        name="users:list",
        summary="List Users",
        description="Retrieve the users.",
        path="/api/users",
        cache=60,
    )
    async def list_users(
        self,
        users_service: UserService,
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> OffsetPagination[schemas.User]:
        """List users."""
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
        users_service: UserService,
        user_id: Annotated[
            UUID,
            Parameter(
                title="User ID",
                description="The user to retrieve.",
            ),
        ],
    ) -> schemas.User:
        """Get a user."""
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
        users_service: UserService,
        data: schemas.UserCreate,
    ) -> schemas.User:
        """Create a new user."""
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
        users_service: UserService,
        user_id: UUID = Parameter(
            title="User ID",
            description="The user to update.",
        ),
    ) -> schemas.User:
        """Create a new user."""
        db_obj = await users_service.update(item_id=user_id, data=data)
        return users_service.to_schema(db_obj, schema_type=schemas.User)

    @delete(
        operation_id="DeleteUser",
        name="users:delete",
        path="/api/users/{user_id:uuid}",
        summary="Remove User",
        description="Removes a user and all associated data from the system.",
    )
    async def delete_user(
        self,
        users_service: UserService,
        user_id: Annotated[
            UUID,
            Parameter(
                title="User ID",
                description="The user to delete.",
            ),
        ],
    ) -> None:
        """Delete a user from the system."""
        _ = await users_service.delete(user_id)

"""User Account Controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any
from uuid import UUID

from advanced_alchemy.extensions.litestar.providers import create_filter_dependencies
from advanced_alchemy.utils.text import slugify
from litestar import Controller, Request, delete, get, patch, post
from litestar.di import Provide
from litestar.params import Dependency, Parameter
from litestar.repository.exceptions import ConflictError
from litestar_vite.inertia import InertiaExternalRedirect, InertiaRedirect, flash, share

from app.config import github_oauth2_client, google_oauth2_client
from app.db.models import TokenType
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
    requires_registration_enabled,
    requires_superuser,
)
from app.domain.accounts.schemas import (
    AccountLogin,
    AccountRegister,
    EmailSent,
    ForgotPasswordRequest,
    PasswordReset,
    PasswordResetToken,
    PasswordUpdate,
    ProfileUpdate,
    User,
    UserCreate,
    UserRoleAdd,
    UserRoleRevoke,
    UserUpdate,
)
from app.domain.accounts.services import (
    EmailTokenService,
    RoleService,
    UserOAuthAccountService,
    UserRoleService,
    UserService,
    provide_email_token_service,
)
from app.lib.oauth import AccessTokenState
from app.lib.schema import Message, NoProps

if TYPE_CHECKING:
    from advanced_alchemy.filters import FilterTypes
    from advanced_alchemy.service.pagination import OffsetPagination
    from httpx_oauth.oauth2 import BaseOAuth2

    from app.db.models import User as UserModel


class PasswordResetController(Controller):
    """Password reset and forgot password flows."""

    include_in_schema = False
    dependencies = {
        "users_service": Provide(provide_users_service),
        "email_token_service": Provide(provide_email_token_service),
    }
    signature_namespace = {
        "UserService": UserService,
        "EmailTokenService": EmailTokenService,
        "ForgotPasswordRequest": ForgotPasswordRequest,
        "PasswordReset": PasswordReset,
    }
    exclude_from_auth = True

    @get(component="auth/forgot-password", name="forgot-password", path="/forgot-password/")
    async def show_forgot_password(self, request: Request) -> InertiaRedirect | NoProps:
        """Show the forgot password form.

        Returns:
            Redirect to dashboard if authenticated, otherwise empty page props.
        """
        if request.session.get("user_id", False):
            flash(request, "You are already logged in.", category="info")
            return InertiaRedirect(request, request.url_for("dashboard"))
        return NoProps()

    @post(component="auth/forgot-password", name="forgot-password.send", path="/forgot-password/", status_code=200)
    async def send_reset_email(self, request: Request, data: ForgotPasswordRequest) -> EmailSent:
        """Request a password reset email.

        Returns:
            Email sent confirmation (always succeeds to prevent enumeration).
        """
        # Always show success message to prevent email enumeration
        request.app.emit(
            event_id="password_reset_requested",
            email=data.email,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent"),
        )
        flash(request, "If an account exists with that email, you will receive a password reset link.", category="info")
        return EmailSent()

    @get(component="auth/reset-password", name="reset-password", path="/reset-password/")
    async def show_reset_password(
        self,
        request: Request,
        email_token_service: EmailTokenService,
        token: str | None = None,
        email: str | None = None,
    ) -> InertiaRedirect | PasswordResetToken:
        """Show the reset password form.

        Returns:
            Redirect if authenticated or invalid token, otherwise token data for form.
        """
        if request.session.get("user_id", False):
            flash(request, "You are already logged in.", category="info")
            return InertiaRedirect(request, request.url_for("dashboard"))

        if not token or not email:
            flash(request, "Invalid password reset link.", category="error")
            return InertiaRedirect(request, request.url_for("forgot-password"))

        # Validate token without consuming it
        token_record = await email_token_service.validate_token(
            plain_token=token, token_type=TokenType.PASSWORD_RESET, email=email,
        )

        if not token_record:
            flash(request, "This password reset link is invalid or has expired.", category="error")
            return InertiaRedirect(request, request.url_for("forgot-password"))

        return PasswordResetToken(token=token, email=email)

    @post(component="auth/reset-password", name="reset-password.update", path="/reset-password/")
    async def reset_password(
        self, request: Request, users_service: UserService, email_token_service: EmailTokenService, data: PasswordReset,
    ) -> InertiaRedirect:
        """Reset the user's password.

        Returns:
            Redirect to login page on success, or forgot-password on failure.
        """
        # Consume the token (validates and marks as used)
        token_record = await email_token_service.consume_token(
            plain_token=data.token, token_type=TokenType.PASSWORD_RESET,
        )

        if not token_record:
            flash(request, "This password reset link is invalid or has expired.", category="error")
            return InertiaRedirect(request, request.url_for("forgot-password"))

        # Update the user's password
        user = await users_service.get_one_or_none(email=token_record.email)
        if not user:
            flash(request, "User not found.", category="error")
            return InertiaRedirect(request, request.url_for("forgot-password"))

        await users_service.reset_password(data.password, db_obj=user)

        # Emit event for confirmation email
        request.app.emit(event_id="password_reset_completed", user_id=user.id)

        flash(request, "Your password has been reset successfully. Please log in.", category="success")
        return InertiaRedirect(request, request.url_for("login"))


class EmailVerificationController(Controller):
    """Email verification flows."""

    include_in_schema = False
    dependencies = {
        "users_service": Provide(provide_users_service),
        "email_token_service": Provide(provide_email_token_service),
    }
    signature_namespace = {
        "UserService": UserService,
        "EmailTokenService": EmailTokenService,
    }
    exclude_from_auth = True

    @get(component="auth/verify-email", name="verify-email", path="/verify-email")
    async def verify_email(
        self,
        request: Request,
        users_service: UserService,
        email_token_service: EmailTokenService,
        token: str | None = None,
    ) -> InertiaRedirect:
        """Verify a user's email address.

        Returns:
            Redirect to login page with appropriate flash message.
        """
        if not token:
            flash(request, "Invalid verification link.", category="error")
            return InertiaRedirect(request, request.url_for("login"))

        # Consume the token (validates and marks as used)
        token_record = await email_token_service.consume_token(
            plain_token=token, token_type=TokenType.EMAIL_VERIFICATION,
        )

        if not token_record:
            flash(request, "This verification link is invalid or has expired.", category="error")
            return InertiaRedirect(request, request.url_for("login"))

        # Mark the user as verified
        user = await users_service.get_one_or_none(email=token_record.email)
        if not user:
            flash(request, "User not found.", category="error")
            return InertiaRedirect(request, request.url_for("login"))

        if user.is_verified:
            flash(request, "Your email is already verified.", category="info")
        else:
            await users_service.update({"is_verified": True}, item_id=user.id, auto_commit=True)
            # Emit event for welcome email
            request.app.emit(event_id="user_verified", user_id=user.id)
            flash(request, "Your email has been verified successfully!", category="success")

        # If user is already logged in, redirect to dashboard
        if request.session.get("user_id"):
            return InertiaRedirect(request, request.url_for("dashboard"))

        return InertiaRedirect(request, request.url_for("login"))


class AccessController(Controller):
    """User login and registration."""

    include_in_schema = False
    dependencies = {"users_service": Provide(provide_users_service)}
    signature_namespace = {"UserService": UserService, "AccountLogin": AccountLogin}
    cache = False
    exclude_from_auth = True

    @get(component="auth/login", name="login", path="/login/")
    async def show_login(self, request: Request) -> InertiaRedirect | NoProps:
        """Show the user login page.

        Returns:
            Redirect to dashboard if authenticated, otherwise empty page props.
        """
        if request.session.get("user_id", False):
            flash(request, "Your account is already authenticated.", category="info")
            return InertiaRedirect(request, request.url_for("dashboard"))
        return NoProps()

    @post(component="auth/login", name="login.check", path="/login/")
    async def login(
        self, request: Request[Any, Any, Any], users_service: UserService, data: AccountLogin,
    ) -> InertiaRedirect:
        """Authenticate a user.

        Returns:
            Redirect to dashboard on successful authentication.
        """
        user = await users_service.authenticate(data.username, data.password)
        request.set_session({"user_id": user.email})
        flash(request, "Your account was successfully authenticated.", category="info")
        request.logger.info("Redirecting to %s ", request.url_for("dashboard"))
        return InertiaRedirect(request, request.url_for("dashboard"))

    @post(name="logout", path="/logout/", exclude_from_auth=False)
    async def logout(self, request: Request) -> InertiaRedirect:
        """Log out the current user.

        Returns:
            Redirect to login page.
        """
        flash(request, "You have been logged out.", category="info")
        request.clear_session()
        return InertiaRedirect(request, request.url_for("login"))


class RegistrationController(Controller):
    """User registration controller.

    Note: OAuth login endpoints bypass registration guard since they're also
    used for existing user login, not just registration.
    """

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
        "AccountRegister": AccountRegister,
    }
    exclude_from_auth = True

    @get(component="auth/register", name="register", path="/register/", guards=[requires_registration_enabled])
    async def show_signup(self, request: Request) -> InertiaRedirect | NoProps:
        """Show the user registration page.

        Returns:
            Redirect to dashboard if authenticated, otherwise empty page props.
        """
        if request.session.get("user_id", False):
            flash(request, "Your account is already authenticated.  Welcome back!", category="info")
            return InertiaRedirect(request, request.url_for("dashboard"))
        return NoProps()

    @post(component="auth/register", name="register.add", path="/register/", guards=[requires_registration_enabled])
    async def signup(
        self, request: Request, users_service: UserService, roles_service: RoleService, data: AccountRegister,
    ) -> InertiaRedirect:
        """Register a new user account.

        Returns:
            Redirect to dashboard on successful registration.
        """
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
        """Redirect to the GitHub login page.

        Returns:
            External redirect to GitHub OAuth authorization URL.
        """
        redirect_to = await github_oauth2_client.get_authorization_url(redirect_uri=request.url_for("github.complete"))
        return InertiaExternalRedirect(request, redirect_to=redirect_to)

    @get(
        name="github.complete",
        path="/o/github/complete/",
        dependencies={"access_token_state": Provide(github_oauth_callback)},
        signature_namespace={"AccessTokenState": AccessTokenState},
    )
    async def github_complete(
        self, request: Request, access_token_state: AccessTokenState, users_service: UserService,
    ) -> InertiaRedirect:
        """Complete login with GitHub and redirect to the dashboard.

        Returns:
            Redirect to dashboard after successful OAuth authentication.
        """
        return await self._auth_complete(request, access_token_state, users_service, github_oauth2_client)

    @post(name="google.register", path="/register/google/")
    async def google_signup(self, request: Request) -> InertiaExternalRedirect:
        """Redirect to the Google login page.

        Returns:
            External redirect to Google OAuth authorization URL.
        """
        redirect_to = await google_oauth2_client.get_authorization_url(redirect_uri=request.url_for("google.complete"))
        return InertiaExternalRedirect(request, redirect_to=redirect_to)

    @get(
        name="google.complete",
        path="/o/google/complete/",
        dependencies={"access_token_state": Provide(google_oauth_callback)},
        signature_namespace={"AccessTokenState": AccessTokenState},
    )
    async def google_complete(
        self, request: Request, access_token_state: AccessTokenState, users_service: UserService,
    ) -> InertiaRedirect:
        """Complete login with Google and redirect to the dashboard.

        Returns:
            Redirect to dashboard after successful OAuth authentication.
        """
        return await RegistrationController._auth_complete(
            request, access_token_state, users_service, google_oauth2_client,
        )

    @staticmethod
    async def _auth_complete(
        request: Request, access_token_state: AccessTokenState, users_service: UserService, oauth_client: BaseOAuth2,
    ) -> InertiaRedirect:
        """Complete the OAuth2 flow and redirect to the dashboard.

        Returns:
            Redirect to dashboard after creating or updating user from OAuth data.
        """
        token, _ = access_token_state
        id_, email = await oauth_client.get_id_email(token=token["access_token"])
        user, created = await users_service.get_or_upsert(
            match_fields=["email"], email=email, is_verified=True, is_active=True,
        )
        request.set_session({"user_id": user.email})
        request.logger.info("auth request complete", id=id_, email=email, provider=oauth_client.name)
        if created:
            request.logger.info("created a new user", id=user.id)
            flash(request, "Welcome to fullstack.  Your account is ready", category="info")
        share(request, "auth", {"isAuthenticated": True, "user": users_service.to_schema(user, schema_type=User)})
        return InertiaRedirect(request, redirect_to=request.url_for("dashboard"))


class ProfileController(Controller):
    include_in_schema = False
    dependencies = {"users_service": Provide(provide_users_service)}
    signature_namespace = {
        "UserService": UserService,
        "User": User,
        "ProfileUpdate": ProfileUpdate,
        "PasswordUpdate": PasswordUpdate,
    }
    guards = [requires_active_user]

    @get(component="profile/edit", name="profile.show", path="/profile/")
    async def profile(self, current_user: UserModel, users_service: UserService) -> User:
        """Display the user profile page.

        Returns:
            Current user data for profile display.
        """
        return users_service.to_schema(current_user, schema_type=User)

    @patch(component="profile/edit", name="profile.update", path="/profile/")
    async def update_profile(self, current_user: UserModel, data: ProfileUpdate, users_service: UserService) -> User:
        """Update the current user's profile information.

        Returns:
            Updated user data.
        """
        db_obj = await users_service.update(data, item_id=current_user.id)
        return users_service.to_schema(db_obj, schema_type=User)

    @patch(component="profile/edit", name="password.update", path="/profile/password-update/")
    async def update_password(
        self, current_user: UserModel, data: PasswordUpdate, users_service: UserService,
    ) -> Message:
        """Update the current user's password.

        Returns:
            Success message confirming password update.
        """
        await users_service.update_password(data.to_dict(), db_obj=current_user)
        return Message(message="Your password was successfully modified.")

    @delete(name="account.remove", path="/profile/", status_code=303)
    async def remove_account(
        self, request: Request, current_user: UserModel, users_service: UserService,
    ) -> InertiaRedirect:
        """Remove the current user's account from the system.

        Returns:
            Redirect to landing page after account deletion.
        """
        request.session.clear()
        _ = await users_service.delete(current_user.id)
        flash(request, "Your account has been removed from the system.", category="info")
        return InertiaRedirect(request, request.url_for("landing"))


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


class UserController(Controller):
    """User Account Controller."""

    tags = ["User Accounts"]
    guards = [requires_superuser]
    dependencies = {"users_service": Provide(provide_users_service)} | create_filter_dependencies({
        "id_filter": UUID,
        "search": "name,email",
        "pagination_type": "limit_offset",
        "pagination_size": 20,
        "created_at": True,
        "updated_at": True,
        "sort_field": "name",
        "sort_order": "asc",
    })
    signature_namespace = {"UserService": UserService, "User": User, "UserUpdate": UserUpdate, "UserCreate": UserCreate}
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
        self, users_service: UserService, filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> OffsetPagination[User]:
        """List users with filtering and pagination.

        Returns:
            Paginated list of users matching the filter criteria.
        """
        results, total = await users_service.list_and_count(*filters)
        return users_service.to_schema(data=results, total=total, schema_type=User, filters=filters)

    @get(
        operation_id="GetUser",
        name="users:get",
        path="/api/users/{user_id:uuid}",
        summary="Retrieve the details of a user.",
    )
    async def get_user(
        self,
        users_service: UserService,
        user_id: Annotated[UUID, Parameter(title="User ID", description="The user to retrieve.")],
    ) -> User:
        """Retrieve a user by ID.

        Returns:
            User data for the requested user.
        """
        db_obj = await users_service.get(user_id)
        return users_service.to_schema(db_obj, schema_type=User)

    @post(
        operation_id="CreateUser",
        name="users:create",
        summary="Create a new user.",
        cache_control=None,
        description="A user who can login and use the system.",
        path="/api/users",
    )
    async def create_user(self, users_service: UserService, data: UserCreate) -> User:
        """Create a new user account.

        Returns:
            Newly created user data.
        """
        db_obj = await users_service.create(data.to_dict())
        return users_service.to_schema(db_obj, schema_type=User)

    @patch(operation_id="UpdateUser", name="users:update", path="/api/users/{user_id:uuid}")
    async def update_user(
        self,
        data: UserUpdate,
        users_service: UserService,
        user_id: UUID = Parameter(title="User ID", description="The user to update."),
    ) -> User:
        """Update an existing user's information.

        Returns:
            Updated user data.
        """
        db_obj = await users_service.update(item_id=user_id, data=data)
        return users_service.to_schema(db_obj, schema_type=User)

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
        user_id: Annotated[UUID, Parameter(title="User ID", description="The user to delete.")],
    ) -> None:
        """Delete a user from the system."""
        _ = await users_service.delete(user_id)

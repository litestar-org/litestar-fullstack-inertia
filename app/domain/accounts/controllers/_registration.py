"""User registration and OAuth controller."""

from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.utils.text import slugify
from litestar import Controller, Request, get, post
from litestar.di import Provide
from litestar.exceptions import ValidationException
from litestar_vite.inertia import InertiaExternalRedirect, InertiaRedirect, flash, share

from app.config import github_oauth2_client, google_oauth2_client
from app.domain.accounts.dependencies import (
    provide_roles_service,
    provide_user_oauth_account_service,
    provide_users_service,
)
from app.domain.accounts.guards import github_oauth_callback, google_oauth_callback, requires_registration_enabled
from app.domain.accounts.schemas import AccountRegister, User
from app.domain.accounts.services import RoleService, UserOAuthAccountService, UserService
from app.lib.oauth import AccessTokenState
from app.lib.schema import NoProps

if TYPE_CHECKING:
    from httpx_oauth.oauth2 import BaseOAuth2

__all__ = ("RegistrationController",)

# Exception messages
_MSG_EMAIL_EXISTS = "A user with this email already exists"


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
            Redirect to dashboard on successful registration, or to invitation page if pending.

        Raises:
            ValidationException: If the email is already registered.
        """
        # Check if email already exists
        existing_user = await users_service.get_one_or_none(email=data.email)
        if existing_user:
            raise ValidationException(_MSG_EMAIL_EXISTS)

        user_data = data.to_dict()
        role_obj = await roles_service.get_one_or_none(slug=slugify(users_service.default_role))
        if role_obj is not None:
            user_data.update({"role_id": role_obj.id})

        invitation_token = request.session.get("invitation_token")

        user = await users_service.create(user_data)
        request.set_session({"user_id": user.email})
        if invitation_token:
            request.session["invitation_token"] = invitation_token

        request.app.emit(event_id="user_created", user_id=user.id)
        flash(request, "Account created successfully.  Welcome!", category="info")

        if invitation_token:
            request.logger.info("Redirecting new user to invitation page with token")
            return InertiaRedirect(request, request.url_for("invitation.accept.page", token=invitation_token))

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
        """Complete the OAuth2 flow and redirect to the dashboard or invitation page.

        Returns:
            Redirect to dashboard or invitation page after creating or updating user from OAuth data.
        """
        token, _ = access_token_state
        id_, email = await oauth_client.get_id_email(token=token["access_token"])

        invitation_token = request.session.get("invitation_token")

        user, created = await users_service.get_or_upsert(
            match_fields=["email"], email=email, is_verified=True, is_active=True,
        )
        request.set_session({"user_id": user.email})
        if invitation_token:
            request.session["invitation_token"] = invitation_token

        request.logger.info("auth request complete", id=id_, email=email, provider=oauth_client.name)
        if created:
            request.logger.info("created a new user", id=user.id)
            flash(request, "Welcome to fullstack.  Your account is ready", category="info")
        share(request, "auth", {"isAuthenticated": True, "user": users_service.to_schema(user, schema_type=User)})

        if invitation_token:
            request.logger.info("Redirecting OAuth user to invitation page with token")
            return InertiaRedirect(request, redirect_to=request.url_for("invitation.accept.page", token=invitation_token))

        return InertiaRedirect(request, redirect_to=request.url_for("dashboard"))

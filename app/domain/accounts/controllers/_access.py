"""User login and logout controller."""

from __future__ import annotations

from typing import Any

from litestar import Controller, Request, get, post
from litestar.di import Provide
from litestar_vite.inertia import InertiaRedirect, flash

from app.domain.accounts.dependencies import provide_users_service
from app.domain.accounts.schemas import AccountLogin
from app.domain.accounts.services import UserService
from app.lib.schema import NoProps

__all__ = ("AccessController",)


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
            Redirect to dashboard on successful authentication,
            to MFA challenge if enabled, or to invitation page if pending.
        """
        user = await users_service.authenticate(data.username, data.password)
        invitation_token = request.session.get("invitation_token")

        # Check if user has MFA enabled
        if user.is_two_factor_enabled and user.totp_secret:
            # Store pending MFA session
            request.set_session({"mfa_user_id": user.email})
            if invitation_token:
                request.session["invitation_token"] = invitation_token
            request.logger.info("Redirecting to MFA challenge")
            return InertiaRedirect(request, request.url_for("mfa-challenge"))

        # No MFA, complete login immediately
        request.set_session({"user_id": user.email})
        if invitation_token:
            request.session["invitation_token"] = invitation_token

        flash(request, "Your account was successfully authenticated.", category="info")

        if invitation_token:
            request.logger.info("Redirecting to invitation page with token")
            return InertiaRedirect(request, request.url_for("invitation.accept.page", token=invitation_token))

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

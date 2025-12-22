"""User login and logout controller."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from litestar import Controller, Request, get, post
from litestar.di import Provide
from litestar.exceptions import PermissionDeniedException, ValidationException
from litestar_vite.inertia import InertiaRedirect, flash
from sqlalchemy.orm import undefer_group

from app.domain.accounts.dependencies import provide_users_service
from app.domain.accounts.schemas import AccountLogin, PasswordConfirm
from app.domain.accounts.services import UserService
from app.lib import crypt
from app.lib.schema import NoProps

__all__ = ("AccessController",)

_MSG_AUTH_REQUIRED = "Authentication required"
_MSG_USER_NOT_FOUND = "User not found"
_MSG_INVALID_CREDENTIALS = "The provided password is incorrect."


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

    @get(component="auth/confirm-password", name="password.confirm.page", path="/confirm-password/", exclude_from_auth=False)
    async def show_confirm_password(self, request: Request) -> NoProps:
        """Show the password confirmation page.

        This is used before sensitive operations to verify the user's identity.

        Returns:
            Empty page props.
        """
        return NoProps()

    @post(component="auth/confirm-password", name="password.confirm", path="/confirm-password/", exclude_from_auth=False)
    async def confirm_password(
        self,
        request: Request,
        users_service: UserService,
        data: PasswordConfirm,
    ) -> InertiaRedirect:
        """Confirm user password before sensitive actions.

        Returns:
            Redirect to intended destination or dashboard.
        """
        user_id = request.session.get("user_id")
        if not user_id:
            raise PermissionDeniedException(_MSG_AUTH_REQUIRED)

        user = await users_service.get_one_or_none(
            email=user_id,
            load=[undefer_group("authentication")],
        )
        if not user:
            raise PermissionDeniedException(_MSG_USER_NOT_FOUND)

        if not user.password_hash or not crypt.verify_password(data.password, user.password_hash):
            raise ValidationException(_MSG_INVALID_CREDENTIALS)

        # Set password confirmation timestamp in session
        request.session["password_confirmed_at"] = datetime.now(UTC).isoformat()

        # Redirect to intended destination or dashboard
        intended_url = request.session.pop("intended_url", None)
        if intended_url:
            return InertiaRedirect(request, intended_url)

        return InertiaRedirect(request, request.url_for("dashboard"))

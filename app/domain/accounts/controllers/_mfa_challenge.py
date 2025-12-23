"""MFA (Multi-Factor Authentication) challenge controller for login flow."""

from __future__ import annotations

from litestar import Controller, Request, get, post
from litestar.di import Provide
from litestar.exceptions import ValidationException
from litestar_vite.inertia import InertiaRedirect, flash

from app.domain.accounts.dependencies import provide_users_service
from app.domain.accounts.schemas import MfaChallenge
from app.domain.accounts.services import UserService
from app.lib.schema import NoProps

__all__ = ("MfaChallengeController",)


class MfaChallengeController(Controller):
    """MFA (Multi-Factor Authentication) challenge during login."""

    path = "/mfa-challenge"
    include_in_schema = False
    dependencies = {"users_service": Provide(provide_users_service)}
    signature_namespace = {"UserService": UserService, "MfaChallenge": MfaChallenge}
    cache = False
    exclude_from_auth = True

    @get(component="auth/mfa-challenge", name="mfa-challenge", path="/")
    async def show_challenge(self, request: Request) -> InertiaRedirect | NoProps:
        """Show the MFA challenge page.

        Returns:
            Redirect if no pending MFA session, otherwise empty props.
        """
        if not request.session.get("mfa_user_id"):
            flash(request, "No MFA challenge pending.", category="warning")
            return InertiaRedirect(request, request.url_for("login"))
        return NoProps()

    @post(component="auth/mfa-challenge", name="mfa-challenge.verify", path="/")
    async def verify_challenge(
        self, request: Request, users_service: UserService, data: MfaChallenge,
    ) -> InertiaRedirect:
        """Verify MFA code during login.

        Raises:
            ValidationException: If the provided code is invalid.

        Returns:
            Redirect to dashboard on success, or back to challenge on failure.
        """
        pending_user = request.session.get("mfa_user_id")
        if not pending_user:
            flash(request, "No MFA challenge pending.", category="warning")
            return InertiaRedirect(request, request.url_for("login"))

        result = await users_service.verify_mfa(
            email=pending_user,
            code=data.code,
            recovery_code=data.recovery_code,
        )

        if not result.verified:
            msg = "Invalid authentication code"
            raise ValidationException(msg)

        invitation_token = request.session.get("invitation_token")
        request.session.pop("mfa_user_id", None)
        request.set_session({"user_id": result.user.email})

        if invitation_token:
            request.session["invitation_token"] = invitation_token

        if result.mfa_disabled:
            flash(request, "Your account was successfully authenticated.", category="info")
        elif result.used_backup_code:
            if result.remaining_backup_codes <= 2:
                flash(
                    request,
                    f"You used a recovery code. Only {result.remaining_backup_codes} code(s) remaining. "
                    "Please regenerate your backup codes.",
                    category="warning",
                )
            else:
                flash(request, "Successfully authenticated with recovery code.", category="info")
        else:
            flash(request, "Your account was successfully authenticated.", category="info")

        if invitation_token:
            return InertiaRedirect(request, request.url_for("invitation.accept.page", token=invitation_token))
        return InertiaRedirect(request, request.url_for("dashboard"))

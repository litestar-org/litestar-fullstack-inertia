"""Email verification controller."""

from __future__ import annotations

from litestar import Controller, Request, get
from litestar.di import Provide
from litestar_vite.inertia import InertiaRedirect, flash

from app.db.models import TokenType
from app.domain.accounts.dependencies import provide_email_token_service, provide_users_service
from app.domain.accounts.services import EmailTokenService, UserService

__all__ = ("EmailVerificationController",)


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

        token_record = await email_token_service.consume_token(
            plain_token=token, token_type=TokenType.EMAIL_VERIFICATION,
        )

        if not token_record:
            flash(request, "This verification link is invalid or has expired.", category="error")
            return InertiaRedirect(request, request.url_for("login"))

        user = await users_service.get_one_or_none(email=token_record.email)
        if not user:
            flash(request, "User not found.", category="error")
            return InertiaRedirect(request, request.url_for("login"))

        if user.is_verified:
            flash(request, "Your email is already verified.", category="info")
        else:
            await users_service.update({"is_verified": True}, item_id=user.id, auto_commit=True)
            request.app.emit(event_id="user_verified", user_id=user.id)
            flash(request, "Your email has been verified successfully!", category="success")

        if request.session.get("user_id"):
            return InertiaRedirect(request, request.url_for("dashboard"))

        return InertiaRedirect(request, request.url_for("login"))

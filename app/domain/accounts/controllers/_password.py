"""Password reset and forgot password controllers."""

from __future__ import annotations

from litestar import Controller, Request, get, post
from litestar.di import Provide
from litestar_vite.inertia import InertiaRedirect, flash

from app.db.models import TokenType
from app.domain.accounts.dependencies import provide_users_service
from app.domain.accounts.schemas import EmailSent, ForgotPasswordRequest, PasswordReset, PasswordResetToken
from app.domain.accounts.services import EmailTokenService, UserService, provide_email_token_service
from app.lib.schema import NoProps

__all__ = ("PasswordResetController",)


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
        token_record = await email_token_service.consume_token(
            plain_token=data.token, token_type=TokenType.PASSWORD_RESET,
        )

        if not token_record:
            flash(request, "This password reset link is invalid or has expired.", category="error")
            return InertiaRedirect(request, request.url_for("forgot-password"))

        user = await users_service.get_one_or_none(email=token_record.email)
        if not user:
            flash(request, "User not found.", category="error")
            return InertiaRedirect(request, request.url_for("forgot-password"))

        await users_service.reset_password(data.password, db_obj=user)
        request.app.emit(event_id="password_reset_completed", user_id=user.id)

        flash(request, "Your password has been reset successfully. Please log in.", category="success")
        return InertiaRedirect(request, request.url_for("login"))

"""Email verification controller."""

from __future__ import annotations

from datetime import timedelta

from litestar import Controller, Request, get, post
from litestar.di import Provide
from litestar.exceptions import PermissionDeniedException
from litestar_vite.inertia import InertiaRedirect, flash

from app.db.models import TokenType
from app.domain.accounts.dependencies import provide_email_token_service, provide_users_service
from app.domain.accounts.services import EmailTokenService, UserService
from app.lib.email import EmailService
from app.lib.settings import get_settings

__all__ = ("EmailVerificationController",)


class EmailVerificationController(Controller):
    """Email verification flows."""

    include_in_schema = False
    dependencies = {
        "users_service": Provide(provide_users_service),
        "email_token_service": Provide(provide_email_token_service),
    }
    signature_namespace = {"UserService": UserService, "EmailTokenService": EmailTokenService}
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

    @post(component="auth/verify-email", name="verification.send", path="/verify-email/send")
    async def resend_verification_email(
        self, request: Request, users_service: UserService, email_token_service: EmailTokenService,
    ) -> InertiaRedirect:
        """Resend verification email to the current user.

        Raises:
            PermissionDeniedException: If the user is not authenticated.

        Returns:
            Redirect back to verify-email page with status message.
        """
        user_id = request.session.get("user_id")
        if not user_id:
            msg = "Authentication required"
            raise PermissionDeniedException(msg)

        user = await users_service.get_one_or_none(email=user_id)
        if not user:
            msg = "User not found"
            raise PermissionDeniedException(msg)

        if user.is_verified:
            flash(request, "Your email is already verified.", category="info")
            return InertiaRedirect(request, request.url_for("dashboard"))

        # Invalidate any existing verification tokens
        await email_token_service.invalidate_existing_tokens(email=user.email, token_type=TokenType.EMAIL_VERIFICATION)

        # Create new verification token
        settings = get_settings()
        expires_delta = timedelta(hours=settings.email.VERIFICATION_TOKEN_EXPIRES_HOURS)
        _, plain_token = await email_token_service.create_token(
            email=user.email,
            token_type=TokenType.EMAIL_VERIFICATION,
            expires_delta=expires_delta,
            user_id=user.id,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent"),
        )

        # Send verification email
        email_service = EmailService()
        await email_service.send_verification_email(user, plain_token)

        flash(request, "A new verification link has been sent to your email address.", category="success")
        return InertiaRedirect(request, request.url_for("verify-email"))

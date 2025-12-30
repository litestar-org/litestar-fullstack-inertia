"""Email verification controller."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING
from uuid import UUID

from litestar import Controller, Request, get, post
from litestar.di import Provide
from litestar.exceptions import PermissionDeniedException
from litestar_vite.inertia import InertiaRedirect, flash

from app.db.models import TokenType
from app.domain.accounts.dependencies import provide_email_token_service, provide_users_service
from app.domain.accounts.signals import UserInfo
from app.lib.email import EmailService
from app.lib.schema import VerifyEmailPage

if TYPE_CHECKING:
    from app.domain.accounts.services import EmailTokenService, UserService
    from app.lib.settings import Settings

__all__ = ("EmailVerificationController",)


class EmailVerificationController(Controller):
    """Email verification flows."""

    include_in_schema = False
    dependencies = {
        "users_service": Provide(provide_users_service),
        "email_token_service": Provide(provide_email_token_service),
    }
    exclude_from_auth = True

    @get(component="auth/verify-email", name="verify-email", path="/verify-email")
    async def verify_email(
        self,
        request: Request,
        users_service: UserService,
        email_token_service: EmailTokenService,
        token: str | None = None,
    ) -> InertiaRedirect | VerifyEmailPage:
        """Verify a user's email address.

        Returns:
            Verify-email page props when no token is supplied, otherwise a redirect.
        """
        if not token:
            return VerifyEmailPage(status=request.query_params.get("status"))

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
        request.session.pop("unverified_user_id", None)

        if request.session.get("user_id"):
            return InertiaRedirect(request, request.url_for("dashboard"))

        return InertiaRedirect(request, request.url_for("login"))

    @post(component="auth/verify-email", name="verification.send", path="/verify-email/send")
    async def resend_verification_email(
        self, request: Request, settings: Settings, users_service: UserService, email_token_service: EmailTokenService,
    ) -> InertiaRedirect:
        """Resend verification email to the current user.

        Raises:
            PermissionDeniedException: If the user is not authenticated.

        Returns:
            Redirect back to verify-email page with status message.
        """
        user_id = request.session.get("user_id")
        unverified_user_id = request.session.get("unverified_user_id")
        if not user_id and not unverified_user_id:
            msg = "Authentication required"
            raise PermissionDeniedException(msg)

        user = None
        if user_id:
            user = await users_service.get_one_or_none(email=user_id)
        elif unverified_user_id:
            try:
                user = await users_service.get_one_or_none(id=UUID(unverified_user_id))
            except (TypeError, ValueError):
                user = None
        if not user:
            msg = "User not found"
            raise PermissionDeniedException(msg)

        if user.is_verified:
            flash(request, "Your email is already verified.", category="info")
            return InertiaRedirect(request, request.url_for("dashboard"))

        await email_token_service.invalidate_existing_tokens(email=user.email, token_type=TokenType.EMAIL_VERIFICATION)
        expires_delta = timedelta(hours=settings.email.VERIFICATION_TOKEN_EXPIRES_HOURS)
        _, plain_token = await email_token_service.create_token(
            email=user.email,
            token_type=TokenType.EMAIL_VERIFICATION,
            expires_delta=expires_delta,
            user_id=user.id,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent"),
        )

        email_service = EmailService()
        user_info = UserInfo(email=user.email, name=user.name)
        await email_service.send_verification_email(user_info, plain_token)

        flash(request, "A new verification link has been sent to your email address.", category="success")
        return InertiaRedirect(request, request.url_for("verify-email", status="verification-link-sent"))

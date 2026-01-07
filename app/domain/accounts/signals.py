from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING

import structlog
from litestar.events import listener

from app import config
from app.config import alchemy
from app.db.models import TokenType
from app.domain.accounts.dependencies import provide_users_service
from app.domain.accounts.services import EmailTokenService
from app.domain.web.email import EmailMessageService
from app.lib.settings import get_settings

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
    from uuid import UUID

    from app.domain.accounts.services import UserService

logger = structlog.get_logger()


@dataclass
class UserInfo:
    """Simple container for user data passed to email service."""

    email: str
    name: str | None


@listener("user_created")
async def user_created_event_handler(
    user_id: UUID, send_verification: bool = True, ip_address: str | None = None, user_agent: str | None = None,
) -> None:
    """Executes when a new user is created.

    Sends a verification email to the new user with a secure token.

    Args:
        user_id: The primary key of the user that was created.
        send_verification: Whether to send verification email.
        ip_address: IP address where signup occurred.
        user_agent: User agent from signup request.
    """
    await logger.ainfo("Running post signup flow.", user_id=str(user_id))

    async with alchemy.get_session() as db_session:
        service_provider: AsyncGenerator[UserService, None] = provide_users_service(db_session)
        try:
            users_service = await anext(service_provider)
            user = await users_service.get_one_or_none(id=user_id)
        finally:
            await service_provider.aclose()

        if user is None:
            await logger.aerror("Could not locate the specified user", id=user_id)
            return

        await logger.ainfo("Found user", email=user.email, name=user.name)

        if not send_verification:
            await logger.ainfo("Skipping verification email", user_id=str(user_id))
            return

        # Create verification token and send email
        settings = get_settings()
        token_service = EmailTokenService(session=db_session)

        # Invalidate any existing verification tokens
        await token_service.invalidate_existing_tokens(email=user.email, token_type=TokenType.EMAIL_VERIFICATION)

        # Create new verification token
        expires_delta = timedelta(hours=settings.email.VERIFICATION_TOKEN_EXPIRES_HOURS)
        _, plain_token = await token_service.create_token(
            email=user.email,
            token_type=TokenType.EMAIL_VERIFICATION,
            expires_delta=expires_delta,
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Send verification email using litestar-email plugin
        async with config.email.provide_service() as mailer:
            email_service = EmailMessageService(mailer=mailer)
            user_info = UserInfo(email=user.email, name=user.name)
            sent = await email_service.send_verification_email(user_info, plain_token)

        if sent:
            await logger.ainfo("Verification email sent", email=user.email)
        else:
            await logger.awarning("Failed to send verification email", email=user.email)


@listener("user_verified")
async def user_verified_event_handler(user_id: UUID) -> None:
    """Executes when a user verifies their email.

    Sends a welcome email to the newly verified user.

    Args:
        user_id: The primary key of the user that was verified.
    """
    await logger.ainfo("User verified, sending welcome email.", user_id=str(user_id))

    async with alchemy.get_session() as db_session:
        service_provider: AsyncGenerator[UserService, None] = provide_users_service(db_session)
        try:
            users_service = await anext(service_provider)
            user = await users_service.get_one_or_none(id=user_id)
        finally:
            await service_provider.aclose()

        if user is None:
            await logger.aerror("Could not locate the specified user", id=user_id)
            return

        # Send welcome email using litestar-email plugin
        async with config.email.provide_service() as mailer:
            email_service = EmailMessageService(mailer=mailer)
            user_info = UserInfo(email=user.email, name=user.name)
            sent = await email_service.send_welcome_email(user_info)

        if sent:
            await logger.ainfo("Welcome email sent", email=user.email)
        else:
            await logger.awarning("Failed to send welcome email", email=user.email)


@listener("password_reset_requested")
async def password_reset_requested_handler(
    email: str, ip_address: str = "unknown", user_agent: str | None = None,
) -> None:
    """Executes when a password reset is requested.

    Creates a reset token and sends the password reset email.
    If the email doesn't exist, logs but doesn't reveal this to caller.

    Args:
        email: The email address for password reset.
        ip_address: IP address where reset was requested.
        user_agent: User agent from the request.
    """
    await logger.ainfo("Password reset requested", email=email)

    async with alchemy.get_session() as db_session:
        service_provider: AsyncGenerator[UserService, None] = provide_users_service(db_session)
        try:
            users_service = await anext(service_provider)
            user = await users_service.get_one_or_none(email=email)
        finally:
            await service_provider.aclose()

        if user is None:
            # Don't reveal if email exists or not
            await logger.ainfo("Password reset for unknown email (not revealing)", email=email)
            return

        # Create reset token and send email
        settings = get_settings()
        token_service = EmailTokenService(session=db_session)

        # Invalidate any existing reset tokens
        await token_service.invalidate_existing_tokens(email=user.email, token_type=TokenType.PASSWORD_RESET)

        # Create new reset token
        expires_delta = timedelta(minutes=settings.email.PASSWORD_RESET_TOKEN_EXPIRES_MINUTES)
        _, plain_token = await token_service.create_token(
            email=user.email,
            token_type=TokenType.PASSWORD_RESET,
            expires_delta=expires_delta,
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Send password reset email using litestar-email plugin
        async with config.email.provide_service() as mailer:
            email_service = EmailMessageService(mailer=mailer)
            user_info = UserInfo(email=user.email, name=user.name)
            sent = await email_service.send_password_reset_email(user_info, plain_token, ip_address)

        if sent:
            await logger.ainfo("Password reset email sent", email=user.email)
        else:
            await logger.awarning("Failed to send password reset email", email=user.email)


@listener("password_reset_completed")
async def password_reset_completed_handler(user_id: UUID) -> None:
    """Executes when a password reset is completed.

    Sends a confirmation email to the user.

    Args:
        user_id: The primary key of the user whose password was reset.
    """
    await logger.ainfo("Password reset completed", user_id=str(user_id))

    async with alchemy.get_session() as db_session:
        service_provider: AsyncGenerator[UserService, None] = provide_users_service(db_session)
        try:
            users_service = await anext(service_provider)
            user = await users_service.get_one_or_none(id=user_id)
        finally:
            await service_provider.aclose()

        if user is None:
            await logger.aerror("Could not locate the specified user", id=user_id)
            return

        # Send confirmation email using litestar-email plugin
        async with config.email.provide_service() as mailer:
            email_service = EmailMessageService(mailer=mailer)
            user_info = UserInfo(email=user.email, name=user.name)
            sent = await email_service.send_password_reset_confirmation_email(user_info)

        if sent:
            await logger.ainfo("Password reset confirmation sent", email=user.email)
        else:
            await logger.awarning("Failed to send password reset confirmation", email=user.email)

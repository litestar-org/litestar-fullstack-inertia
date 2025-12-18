"""Tests for password reset flow and email token service."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

import pytest

from app.db.models import TokenType
from app.domain.accounts.services import EmailTokenService, UserService

if TYPE_CHECKING:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

pytestmark = pytest.mark.anyio


# Password Reset Controller Tests


async def test_forgot_password_page_loads(client: "AsyncClient") -> None:
    """Forgot password page should load for unauthenticated users."""
    response = await client.get("/forgot-password/")
    assert response.status_code == 200


async def test_forgot_password_submit_existing_email(client: "AsyncClient") -> None:
    """Submitting forgot password with existing email should succeed."""
    # Get CSRF token
    response = await client.get("/forgot-password/")
    csrf_token: str = response.cookies.get("XSRF-TOKEN") or ""

    headers = {
        "X-XSRF-TOKEN": csrf_token,
        "Content-Type": "application/json",
    }

    response = await client.post(
        "/forgot-password/",
        json={"email": "user@example.com"},
        headers=headers,
    )
    # Should succeed (we don't reveal if email exists)
    assert response.status_code == 200


async def test_forgot_password_submit_nonexistent_email(client: "AsyncClient") -> None:
    """Submitting forgot password with nonexistent email should still succeed.

    This prevents email enumeration attacks.
    """
    response = await client.get("/forgot-password/")
    csrf_token: str = response.cookies.get("XSRF-TOKEN") or ""

    headers = {
        "X-XSRF-TOKEN": csrf_token,
        "Content-Type": "application/json",
    }

    response = await client.post(
        "/forgot-password/",
        json={"email": "nonexistent@example.com"},
        headers=headers,
    )
    # Should still succeed to prevent enumeration
    assert response.status_code == 200


async def test_reset_password_page_without_token(client: "AsyncClient") -> None:
    """Reset password page without token should redirect to forgot password."""
    response = await client.get("/reset-password/", follow_redirects=False)
    # Should redirect to forgot-password (307 is Inertia's redirect status)
    assert response.status_code in (302, 303, 307)


async def test_reset_password_page_with_invalid_token(client: "AsyncClient") -> None:
    """Reset password page with invalid token should redirect."""
    response = await client.get(
        "/reset-password/",
        params={"token": "invalid-token", "email": "user@example.com"},
        follow_redirects=False,
    )
    # Should redirect since token is invalid (307 is Inertia's redirect status)
    assert response.status_code in (302, 303, 307)


# Email Token Service Tests


async def test_email_token_create_and_validate(
    sessionmaker: "async_sessionmaker[AsyncSession]",
) -> None:
    """Token can be created and validated."""
    async with sessionmaker() as session:
        service = EmailTokenService(session=session)

        # Create token
        token_record, plain_token = await service.create_token(
            email="user@example.com",
            token_type=TokenType.PASSWORD_RESET,
            expires_delta=timedelta(hours=1),
        )

        assert token_record is not None
        assert plain_token is not None
        assert token_record.email == "user@example.com"
        assert token_record.token_type == TokenType.PASSWORD_RESET
        assert token_record.is_valid is True

        # Validate token
        validated = await service.validate_token(
            plain_token=plain_token,
            token_type=TokenType.PASSWORD_RESET,
        )

        assert validated is not None
        assert validated.id == token_record.id


async def test_email_token_validate_wrong_type(
    sessionmaker: "async_sessionmaker[AsyncSession]",
) -> None:
    """Token validation fails with wrong token type."""
    async with sessionmaker() as session:
        service = EmailTokenService(session=session)

        # Create password reset token
        _, plain_token = await service.create_token(
            email="user@example.com",
            token_type=TokenType.PASSWORD_RESET,
            expires_delta=timedelta(hours=1),
        )

        # Try to validate as email verification token
        validated = await service.validate_token(
            plain_token=plain_token,
            token_type=TokenType.EMAIL_VERIFICATION,
        )

        assert validated is None


async def test_email_token_validate_wrong_email(
    sessionmaker: "async_sessionmaker[AsyncSession]",
) -> None:
    """Token validation fails with wrong email."""
    async with sessionmaker() as session:
        service = EmailTokenService(session=session)

        _, plain_token = await service.create_token(
            email="user@example.com",
            token_type=TokenType.PASSWORD_RESET,
            expires_delta=timedelta(hours=1),
        )

        validated = await service.validate_token(
            plain_token=plain_token,
            token_type=TokenType.PASSWORD_RESET,
            email="other@example.com",
        )

        assert validated is None


async def test_email_token_consume(
    sessionmaker: "async_sessionmaker[AsyncSession]",
) -> None:
    """Token can be consumed only once."""
    async with sessionmaker() as session:
        service = EmailTokenService(session=session)

        _, plain_token = await service.create_token(
            email="user@example.com",
            token_type=TokenType.PASSWORD_RESET,
            expires_delta=timedelta(hours=1),
        )

        # First consume should succeed
        consumed = await service.consume_token(
            plain_token=plain_token,
            token_type=TokenType.PASSWORD_RESET,
        )
        assert consumed is not None
        assert consumed.used_at is not None

        # Second consume should fail
        consumed_again = await service.consume_token(
            plain_token=plain_token,
            token_type=TokenType.PASSWORD_RESET,
        )
        assert consumed_again is None


async def test_email_token_expired(
    sessionmaker: "async_sessionmaker[AsyncSession]",
) -> None:
    """Expired token cannot be validated."""
    async with sessionmaker() as session:
        service = EmailTokenService(session=session)

        # Create already-expired token
        token_record, plain_token = await service.create_token(
            email="user@example.com",
            token_type=TokenType.PASSWORD_RESET,
            expires_delta=timedelta(hours=-1),  # Already expired
        )

        # Token should exist but not be valid
        assert token_record is not None

        validated = await service.validate_token(
            plain_token=plain_token,
            token_type=TokenType.PASSWORD_RESET,
        )
        assert validated is None


async def test_email_token_invalidate_existing(
    sessionmaker: "async_sessionmaker[AsyncSession]",
) -> None:
    """Can invalidate all existing tokens of a type for an email."""
    async with sessionmaker() as session:
        service = EmailTokenService(session=session)

        # Create multiple tokens
        _, token1 = await service.create_token(
            email="user@example.com",
            token_type=TokenType.PASSWORD_RESET,
            expires_delta=timedelta(hours=1),
        )
        _, token2 = await service.create_token(
            email="user@example.com",
            token_type=TokenType.PASSWORD_RESET,
            expires_delta=timedelta(hours=1),
        )

        # Invalidate all
        count = await service.invalidate_existing_tokens(
            email="user@example.com",
            token_type=TokenType.PASSWORD_RESET,
        )
        assert count == 2

        # Both tokens should now be invalid
        assert await service.validate_token(token1, TokenType.PASSWORD_RESET) is None
        assert await service.validate_token(token2, TokenType.PASSWORD_RESET) is None


async def test_email_token_with_metadata(
    sessionmaker: "async_sessionmaker[AsyncSession]",
) -> None:
    """Token can store additional metadata."""
    async with sessionmaker() as session:
        service = EmailTokenService(session=session)

        token_record, _ = await service.create_token(
            email="user@example.com",
            token_type=TokenType.PASSWORD_RESET,
            expires_delta=timedelta(hours=1),
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            metadata={"source": "forgot_password_form"},
        )

        assert token_record.ip_address == "192.168.1.1"
        assert token_record.user_agent == "Mozilla/5.0"
        assert token_record.metadata_.get("source") == "forgot_password_form"


# User Service Password Reset Tests


async def test_user_service_reset_password(
    sessionmaker: "async_sessionmaker[AsyncSession]",
) -> None:
    """User password can be reset without knowing current password."""
    async with sessionmaker() as session:
        users_service = UserService(session=session)

        # Get a user
        user = await users_service.get_one_or_none(email="user@example.com")
        assert user is not None
        old_hash = user.hashed_password

        # Reset password
        await users_service.reset_password("NewPassword123!", db_obj=user)

        # Verify password changed
        user_refreshed = await users_service.get_one_or_none(email="user@example.com")
        assert user_refreshed is not None
        assert user_refreshed.hashed_password != old_hash


async def test_user_service_reset_password_inactive_user(
    sessionmaker: "async_sessionmaker[AsyncSession]",
) -> None:
    """Cannot reset password for inactive user."""
    from litestar.exceptions import PermissionDeniedException

    async with sessionmaker() as session:
        users_service = UserService(session=session)

        # Get inactive user
        user = await users_service.get_one_or_none(email="inactive@example.com")
        assert user is not None
        assert user.is_active is False

        # Should raise PermissionDeniedException
        with pytest.raises(PermissionDeniedException):
            await users_service.reset_password("NewPassword123!", db_obj=user)

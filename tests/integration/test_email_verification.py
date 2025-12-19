"""Tests for the EmailVerificationController."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import TokenType
from app.domain.accounts.services import EmailTokenService, UserService

if TYPE_CHECKING:
    from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def test_verify_email_no_token(client: "AsyncClient") -> None:
    """Verify email without token should redirect to login with error."""
    response = await client.get("/verify-email", follow_redirects=True)
    assert response.status_code == 200
    assert "/login" in str(response.url)


async def test_verify_email_invalid_token(client: "AsyncClient") -> None:
    """Verify email with invalid token should redirect to login with error."""
    response = await client.get("/verify-email/?token=invalid-token", follow_redirects=True)
    assert response.status_code == 200
    assert "/login" in str(response.url)


async def test_verify_email_valid_token(
    client: "AsyncClient",
    sessionmaker: "async_sessionmaker[AsyncSession]",
) -> None:
    """Verify email with valid token should mark user as verified."""
    # Create a verification token for an unverified user using a fresh session
    async with sessionmaker() as session:
        users_service = UserService(session=session)
        user = await users_service.get_one(email="user@example.com")
        await users_service.update({"is_verified": False}, item_id=user.id, auto_commit=True)

        token_service = EmailTokenService(session=session)
        _, plain_token = await token_service.create_token(
            email="user@example.com",
            token_type=TokenType.EMAIL_VERIFICATION,
            expires_delta=timedelta(hours=24),
        )
        await session.commit()

    # Verify the email
    response = await client.get(f"/verify-email/?token={plain_token}", follow_redirects=True)
    assert response.status_code == 200
    assert "/login" in str(response.url)

    # Check that user is now verified using a completely fresh session
    async with sessionmaker() as verify_session:
        verify_users_service = UserService(session=verify_session)
        user = await verify_users_service.get_one(email="user@example.com")
        assert user.is_verified is True


async def test_verify_email_already_verified(
    client: "AsyncClient",
    session: AsyncSession,
) -> None:
    """Verify email for already verified user should show info message."""
    users_service = UserService(session=session)
    user = await users_service.get_one(email="user@example.com")
    await users_service.update({"is_verified": True}, item_id=user.id)
    await session.commit()

    token_service = EmailTokenService(session=session)
    _, plain_token = await token_service.create_token(
        email="user@example.com",
        token_type=TokenType.EMAIL_VERIFICATION,
        expires_delta=timedelta(hours=24),
    )
    await session.commit()

    response = await client.get(f"/verify-email/?token={plain_token}", follow_redirects=True)
    assert response.status_code == 200
    assert "/login" in str(response.url)


async def test_verify_email_expired_token(
    client: "AsyncClient",
    session: AsyncSession,
) -> None:
    """Verify email with expired token should redirect to login with error."""
    token_service = EmailTokenService(session=session)
    _, plain_token = await token_service.create_token(
        email="user@example.com",
        token_type=TokenType.EMAIL_VERIFICATION,
        expires_delta=timedelta(hours=-1),  # Already expired
    )
    await session.commit()

    response = await client.get(f"/verify-email/?token={plain_token}", follow_redirects=True)
    assert response.status_code == 200
    assert "/login" in str(response.url)


async def test_verify_email_used_token(
    client: "AsyncClient",
    session: AsyncSession,
) -> None:
    """Verify email with already used token should redirect to login with error."""
    users_service = UserService(session=session)
    user = await users_service.get_one(email="user@example.com")
    await users_service.update({"is_verified": False}, item_id=user.id)
    await session.commit()

    token_service = EmailTokenService(session=session)
    _, plain_token = await token_service.create_token(
        email="user@example.com",
        token_type=TokenType.EMAIL_VERIFICATION,
        expires_delta=timedelta(hours=24),
    )
    await session.commit()

    # Use the token once
    response = await client.get(f"/verify-email/?token={plain_token}", follow_redirects=True)
    assert response.status_code == 200

    # Try to use the same token again - should fail and redirect to login
    response = await client.get(f"/verify-email/?token={plain_token}", follow_redirects=True)
    assert response.status_code == 200
    assert "/login" in str(response.url)

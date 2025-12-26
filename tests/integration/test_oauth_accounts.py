"""Tests for OAuth account management."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.anyio


async def test_unlink_oauth_no_auth(client: "AsyncClient") -> None:
    """Unauthenticated requests to unlink should return 401."""
    response = await client.delete("/profile/oauth/github")
    assert response.status_code == 401


async def test_link_oauth_no_auth(client: "AsyncClient") -> None:
    """Unauthenticated requests to start link should return 401."""
    response = await client.post("/profile/oauth/github/link")
    assert response.status_code == 401


async def test_unlink_unknown_provider(client: "AsyncClient", user_inertia_headers: dict[str, str]) -> None:
    """Unlinking an unknown provider should show error."""
    response = await client.delete(
        "/profile/oauth/unknown",
        headers=user_inertia_headers,
        follow_redirects=False,
    )
    # Should redirect with error flash
    assert response.status_code == 303


async def test_link_unknown_provider(client: "AsyncClient", user_inertia_headers: dict[str, str]) -> None:
    """Linking an unknown provider should return 404."""
    response = await client.post(
        "/profile/oauth/unknown/link",
        headers=user_inertia_headers,
        follow_redirects=False,
    )
    assert response.status_code == 404


async def test_can_unlink_with_password(session: "AsyncSession") -> None:
    """User with password can always unlink OAuth."""
    from app.db.models import User
    from app.domain.accounts.services import UserOAuthAccountService

    # Create a mock user with password
    user = User(
        id=UUID("97108ac1-ffcb-411d-8b1e-d9183399f63b"),
        email="test@example.com",
        hashed_password="hashed_password_here",
    )

    async with UserOAuthAccountService.new(session) as service:
        can_unlink, reason = await service.can_unlink_oauth(user, "github")
        assert can_unlink is True
        assert not reason


async def test_cannot_unlink_only_oauth_no_password(session: "AsyncSession") -> None:
    """User without password and only 1 OAuth cannot unlink."""
    from app.db.models import User, UserOauthAccount
    from app.domain.accounts.services import UserOAuthAccountService

    user_id = UUID("11108ac1-ffcb-411d-8b1e-d9183399f63b")

    # Create user without password
    user = User(
        id=user_id,
        email="oauth-only@example.com",
        hashed_password=None,
    )
    session.add(user)

    # Create one OAuth account
    oauth = UserOauthAccount(
        user_id=user_id,
        oauth_name="github",
        account_id="12345",
        account_email="oauth@github.com",
        access_token="token",
    )
    session.add(oauth)
    await session.commit()

    async with UserOAuthAccountService.new(session) as service:
        can_unlink, reason = await service.can_unlink_oauth(user, "github")
        assert can_unlink is False
        assert "password" in reason.lower()


async def test_can_unlink_multiple_oauth_no_password(session: "AsyncSession") -> None:
    """User without password but multiple OAuth can unlink one."""
    from app.db.models import User, UserOauthAccount
    from app.domain.accounts.services import UserOAuthAccountService

    user_id = UUID("22208ac1-ffcb-411d-8b1e-d9183399f63b")

    # Create user without password
    user = User(
        id=user_id,
        email="multi-oauth@example.com",
        hashed_password=None,
    )
    session.add(user)

    # Create multiple OAuth accounts
    oauth1 = UserOauthAccount(
        user_id=user_id,
        oauth_name="github",
        account_id="gh123",
        account_email="oauth@github.com",
        access_token="token1",
    )
    oauth2 = UserOauthAccount(
        user_id=user_id,
        oauth_name="google",
        account_id="gg456",
        account_email="oauth@google.com",
        access_token="token2",
    )
    session.add(oauth1)
    session.add(oauth2)
    await session.commit()

    async with UserOAuthAccountService.new(session) as service:
        can_unlink, reason = await service.can_unlink_oauth(user, "github")
        assert can_unlink is True
        assert not reason


async def test_link_new_oauth_account(session: "AsyncSession") -> None:
    """Can link a new OAuth account to existing user."""
    from app.db.models import User
    from app.domain.accounts.services import UserOAuthAccountService

    user_id = UUID("33308ac1-ffcb-411d-8b1e-d9183399f63b")

    user = User(
        id=user_id,
        email="link-test@example.com",
        hashed_password="password",
    )
    session.add(user)
    await session.commit()

    async with UserOAuthAccountService.new(session) as service:
        oauth = await service.link_or_update_oauth(
            user_id=user_id,
            provider="github",
            account_id="new123",
            account_email="new@github.com",
            access_token="access_token",
            refresh_token="refresh_token",
            expires_at=1234567890,
            scopes=["read:user", "user:email"],
        )
        assert oauth.oauth_name == "github"
        assert oauth.account_id == "new123"
        assert oauth.account_email == "new@github.com"
        assert oauth.scopes == ["read:user", "user:email"]


async def test_unlink_oauth_account(session: "AsyncSession") -> None:
    """Can unlink an OAuth account."""
    from app.db.models import User, UserOauthAccount
    from app.domain.accounts.services import UserOAuthAccountService

    user_id = UUID("55508ac1-ffcb-411d-8b1e-d9183399f63b")

    user = User(
        id=user_id,
        email="unlink-test@example.com",
        hashed_password="password",
    )
    session.add(user)

    oauth = UserOauthAccount(
        user_id=user_id,
        oauth_name="github",
        account_id="unlink123",
        account_email="unlink@github.com",
        access_token="token",
    )
    session.add(oauth)
    await session.commit()

    async with UserOAuthAccountService.new(session) as service:
        await service.unlink_oauth(user_id, "github")

        # Verify it was deleted
        remaining = await service.count(user_id=user_id)
        assert remaining == 0


async def test_get_by_provider_account_id_exists(session: "AsyncSession") -> None:
    """Can find OAuth account by provider and account_id."""
    from app.db.models import User, UserOauthAccount
    from app.domain.accounts.services import UserOAuthAccountService

    user_id = UUID("66608ac1-ffcb-411d-8b1e-d9183399f63b")

    user = User(
        id=user_id,
        email="find-test@example.com",
        hashed_password="password",
    )
    session.add(user)

    oauth = UserOauthAccount(
        user_id=user_id,
        oauth_name="google",
        account_id="find456",
        account_email="find@google.com",
        access_token="token",
    )
    session.add(oauth)
    await session.commit()

    async with UserOAuthAccountService.new(session) as service:
        found = await service.get_by_provider_account_id("google", "find456")
        assert found is not None
        assert found.user_id == user_id


async def test_get_by_provider_account_id_not_found(session: "AsyncSession") -> None:
    """Returns None for nonexistent OAuth account."""
    from app.domain.accounts.services import UserOAuthAccountService

    async with UserOAuthAccountService.new(session) as service:
        found = await service.get_by_provider_account_id("github", "nonexistent")
        assert found is None

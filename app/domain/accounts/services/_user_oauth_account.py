from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

from app.db.models import UserOauthAccount

if TYPE_CHECKING:
    from uuid import UUID

    from app.db.models import User


class UserOAuthAccountService(SQLAlchemyAsyncRepositoryService[UserOauthAccount]):
    """Handles database operations for user OAuth accounts."""

    class Repo(SQLAlchemyAsyncRepository[UserOauthAccount]):
        """User OAuth Account SQLAlchemy Repository."""

        model_type = UserOauthAccount

    repository_type = Repo

    async def can_unlink_oauth(self, user: User, provider: str) -> tuple[bool, str]:
        """Check if user can safely unlink an OAuth provider.

        Args:
            user: The user attempting to unlink.
            provider: The OAuth provider name (e.g., "github", "google").

        Returns:
            Tuple of (can_unlink, reason_if_not).

        Rules:
            1. If user has a password set, always allow unlink.
            2. If user has no password:
               - Block if this is their only OAuth account.
               - Allow if they have multiple OAuth accounts.
        """
        if user.hashed_password is not None:
            return True, ""

        oauth_count = await self.count(user_id=user.id)
        if oauth_count <= 1:
            return False, "Cannot unlink your only login method. Please set a password first."
        return True, ""

    async def unlink_oauth(self, user_id: UUID, provider: str) -> None:
        """Remove an OAuth account for a user.

        Args:
            user_id: The user's ID.
            provider: The OAuth provider name to unlink.
        """
        oauth_account = await self.get_one_or_none(user_id=user_id, oauth_name=provider)
        if oauth_account:
            await self.delete(oauth_account.id)

    async def link_or_update_oauth(
        self,
        user_id: UUID,
        provider: str,
        account_id: str,
        account_email: str,
        access_token: str,
        refresh_token: str | None = None,
        expires_at: int | None = None,
        scopes: list[str] | None = None,
    ) -> UserOauthAccount:
        """Link a new OAuth account or update existing one.

        If the user already has an account with this provider, update tokens.
        Otherwise, create a new link.

        Args:
            user_id: The user's ID.
            provider: The OAuth provider name.
            account_id: Unique identifier from the OAuth provider.
            account_email: Email from the OAuth provider.
            access_token: OAuth access token.
            refresh_token: OAuth refresh token (optional).
            expires_at: Token expiration timestamp (optional).
            scopes: OAuth scopes granted (optional).

        Returns:
            The created or updated OAuth account record.
        """
        existing = await self.get_one_or_none(user_id=user_id, oauth_name=provider)
        if existing:
            return await self.update(
                data={
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "expires_at": expires_at,
                    "scopes": scopes,
                    "account_email": account_email,
                },
                item_id=existing.id,
            )
        return await self.create(
            data={
                "user_id": user_id,
                "oauth_name": provider,
                "account_id": account_id,
                "account_email": account_email,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_at": expires_at,
                "scopes": scopes,
            },
        )

    async def get_by_provider_account_id(
        self,
        provider: str,
        account_id: str,
    ) -> UserOauthAccount | None:
        """Get an OAuth account by provider and account ID.

        Args:
            provider: The OAuth provider name.
            account_id: The account ID from the provider.

        Returns:
            The OAuth account if found, None otherwise.
        """
        return await self.get_one_or_none(oauth_name=provider, account_id=account_id)

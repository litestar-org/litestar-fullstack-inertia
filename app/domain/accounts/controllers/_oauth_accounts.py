"""OAuth account management controller."""

from __future__ import annotations

import secrets
from typing import TYPE_CHECKING

from litestar import Controller, Request, delete, get, post
from litestar.di import Provide
from litestar.exceptions import NotFoundException, PermissionDeniedException
from litestar_oauth.clients.base import BaseOAuth2
from litestar_vite.inertia import InertiaExternalRedirect, InertiaRedirect, flash

from app.config import github_oauth2_client, google_oauth2_client
from app.domain.accounts.dependencies import provide_user_oauth_account_service, provide_users_service
from app.domain.accounts.guards import requires_active_user
from app.domain.accounts.schemas import User
from app.domain.accounts.services import UserOAuthAccountService, UserService
from app.lib.oauth import AccessTokenState, OAuth2AuthorizeCallback

if TYPE_CHECKING:
    from app.db.models import User as UserModel

__all__ = ("OAuthAccountController",)

OAUTH_CLIENTS: dict[str, BaseOAuth2] = {"github": github_oauth2_client, "google": google_oauth2_client}

OAUTH_DEFAULT_SCOPES: dict[str, list[str]] = {
    "github": ["read:user", "user:email"],
    "google": ["openid", "email", "profile"],
}


def _get_oauth_client(provider: str) -> BaseOAuth2:
    """Get the OAuth client for a provider."""
    if client := OAUTH_CLIENTS.get(provider):
        return client
    raise NotFoundException(detail=f"Unknown OAuth provider: {provider}")


class OAuthAccountController(Controller):
    """OAuth account management for profile settings."""

    path = "/profile/oauth"
    include_in_schema = False
    dependencies = {
        "users_service": Provide(provide_users_service),
        "oauth_account_service": Provide(provide_user_oauth_account_service),
    }
    signature_namespace = {
        "UserService": UserService,
        "UserOAuthAccountService": UserOAuthAccountService,
        "User": User,
        "AccessTokenState": AccessTokenState,
    }
    guards = [requires_active_user]

    @delete(path="/{provider:str}", name="oauth.unlink", status_code=303)
    async def unlink_oauth(
        self, request: Request, provider: str, current_user: UserModel, oauth_account_service: UserOAuthAccountService
    ) -> InertiaRedirect:
        """Unlink an OAuth provider from the user's account.

        Args:
            request: The HTTP request.
            provider: The OAuth provider name (github, google).
            current_user: The authenticated user.
            oauth_account_service: OAuth account service.

        Returns:
            Redirect to profile page.

        Raises:
            PermissionDeniedException: If user cannot unlink (no password, only auth method).
        """
        if provider not in OAUTH_CLIENTS:
            flash(request, f"Unknown OAuth provider: {provider}", category="error")
            return InertiaRedirect(request, request.url_for("profile.show"))

        can_unlink, reason = await oauth_account_service.can_unlink_oauth(current_user, provider)
        if not can_unlink:
            raise PermissionDeniedException(detail=reason)

        await oauth_account_service.unlink_oauth(current_user.id, provider)
        flash(request, f"Successfully disconnected {provider.title()} account.", category="success")
        return InertiaRedirect(request, request.url_for("profile.show"))

    @post(path="/{provider:str}/link", name="oauth.link.start")
    async def start_link_oauth(self, request: Request, provider: str) -> InertiaExternalRedirect:
        """Start the OAuth linking flow.

        Stores the action in session and redirects to OAuth provider.

        Args:
            request: The HTTP request.
            provider: The OAuth provider name.

        Returns:
            External redirect to OAuth provider authorization URL.
        """
        client = _get_oauth_client(provider)
        state_key = f"oauth_state:link:{provider}"
        request.session[state_key] = secrets.token_urlsafe(32)
        redirect_to = await client.get_authorization_url(
            redirect_uri=str(request.url_for("oauth.link.complete", provider=provider)),
            scope=OAUTH_DEFAULT_SCOPES.get(provider, []),
            state=request.session[state_key],
        )
        return InertiaExternalRedirect(request, redirect_to=redirect_to)

    @get(path="/{provider:str}/complete", name="oauth.link.complete")
    async def complete_link_oauth(
        self,
        request: Request,
        provider: str,
        current_user: UserModel,
        oauth_account_service: UserOAuthAccountService,
        users_service: UserService,
    ) -> InertiaRedirect:
        """Complete OAuth linking and redirect to profile.

        Args:
            request: The HTTP request.
            provider: The OAuth provider name.
            current_user: The authenticated user.
            oauth_account_service: OAuth account service.
            users_service: User service.

        Returns:
            Redirect to profile page.
        """
        client = _get_oauth_client(provider)
        state_key = next(
            (
                key
                for key in (f"oauth_state:link:{provider}", f"oauth_state:upgrade:{provider}")
                if key in request.session
            ),
            None,
        )
        if not state_key:
            flash(request, "Invalid OAuth session. Please try again.", category="error")
            return InertiaRedirect(request, request.url_for("profile.show"))
        callback = OAuth2AuthorizeCallback(client, route_name="oauth.link.complete", state_session_key=state_key)
        try:
            access_token_state: AccessTokenState = await callback(request)
        except Exception as e:  # noqa: BLE001
            request.logger.warning("OAuth callback failed", error=str(e), provider=provider)
            flash(request, f"Failed to connect {provider.title()} account. Please try again.", category="error")
            return InertiaRedirect(request, request.url_for("profile.show"))

        token, _ = access_token_state

        try:
            account_id, account_email = await client.get_id_email(token=token["access_token"])
        except Exception as e:  # noqa: BLE001
            request.logger.warning("Failed to get OAuth user info", error=str(e), provider=provider)
            flash(request, f"Failed to get account info from {provider.title()}.", category="error")
            return InertiaRedirect(request, request.url_for("profile.show"))

        if not account_email:
            flash(
                request,
                f"Could not retrieve email from {provider.title()}. Please ensure email access is granted.",
                category="error",
            )
            return InertiaRedirect(request, request.url_for("profile.show"))

        existing = await oauth_account_service.get_by_provider_account_id(provider, account_id)
        if existing and existing.user_id != current_user.id:
            flash(request, f"This {provider.title()} account is already linked to another user.", category="error")
            return InertiaRedirect(request, request.url_for("profile.show"))

        scopes = token.get("scope", "").split() if token.get("scope") else OAUTH_DEFAULT_SCOPES.get(provider)

        await oauth_account_service.link_or_update_oauth(
            user_id=current_user.id,
            provider=provider,
            account_id=account_id,
            account_email=account_email,
            access_token=token["access_token"],
            refresh_token=token.get("refresh_token"),
            expires_at=token.get("expires_at"),
            scopes=scopes,
        )

        flash(request, f"Successfully connected {provider.title()} account.", category="success")
        return InertiaRedirect(request, request.url_for("profile.show"))

    @post(path="/{provider:str}/upgrade-scopes", name="oauth.upgrade_scopes")
    async def upgrade_scopes(self, request: Request, provider: str) -> InertiaExternalRedirect:
        """Request expanded OAuth scopes via re-authorization.

        Args:
            request: The HTTP request.
            provider: The OAuth provider name.

        Returns:
            External redirect to OAuth provider for re-authorization.
        """
        client = _get_oauth_client(provider)
        state_key = f"oauth_state:upgrade:{provider}"
        request.session[state_key] = secrets.token_urlsafe(32)
        redirect_to = await client.get_authorization_url(
            redirect_uri=str(request.url_for("oauth.link.complete", provider=provider)),
            scope=OAUTH_DEFAULT_SCOPES.get(provider, []),
            state=request.session[state_key],
        )
        return InertiaExternalRedirect(request, redirect_to=redirect_to)

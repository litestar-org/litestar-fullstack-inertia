from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from litestar.exceptions import PermissionDeniedException
from litestar.middleware.session.server_side import ServerSideSessionBackend
from litestar.security.session_auth import SessionAuth
from litestar_vite.inertia import share

from app.config import alchemy, github_oauth2_client, google_oauth2_client
from app.config import session as session_config
from app.db.models import User as UserModel
from app.domain.accounts.dependencies import (
    provide_personal_access_token_service,
    provide_user_session_service,
    provide_users_service,
)
from app.domain.accounts.schemas import User as UserSchema
from app.lib.oauth import OAuth2AuthorizeCallback
from app.lib.settings import get_settings

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from litestar.connection import ASGIConnection
    from litestar.handlers.base import BaseRouteHandler

    from app.domain.accounts.services import PersonalAccessTokenService, UserService, UserSessionService


__all__ = (
    "current_user_from_session",
    "requires_active_user",
    "requires_registration_enabled",
    "requires_superuser",
    "requires_token_ability",
    "requires_verified_user",
    "session_auth",
)

_TOKEN_AUTH_SCOPE_KEY = "_token_auth"


@dataclass(slots=True)
class TokenAuthContext:
    token_id: str
    abilities: tuple[str, ...]


def _clear_token_auth(connection: ASGIConnection[Any, Any, Any, Any]) -> None:
    connection.scope.pop(_TOKEN_AUTH_SCOPE_KEY, None)


def _set_token_auth(
    connection: ASGIConnection[Any, Any, Any, Any], *, token_id: str, abilities: list[str],
) -> None:
    connection.scope[_TOKEN_AUTH_SCOPE_KEY] = TokenAuthContext(token_id=token_id, abilities=tuple(abilities))


def get_token_auth_context(connection: ASGIConnection[Any, Any, Any, Any]) -> TokenAuthContext | None:
    """Return bearer-token auth details for the current request, if any."""
    context = connection.scope.get(_TOKEN_AUTH_SCOPE_KEY)
    return context if isinstance(context, TokenAuthContext) else None


def requires_token_ability(required_ability: str):
    """Guard factory for routes that should enforce a bearer-token ability when token auth is used."""

    def guard(connection: ASGIConnection[Any, Any, Any, Any], _: BaseRouteHandler) -> None:
        token_auth = get_token_auth_context(connection)
        if token_auth is None:
            return
        if "*" in token_auth.abilities or required_ability in token_auth.abilities:
            return
        raise PermissionDeniedException(detail=f"Token is missing required ability: {required_ability}")

    return guard


def _get_bearer_token(connection: ASGIConnection[Any, Any, Any, Any]) -> str | None:
    authorization = connection.headers.get("Authorization")
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token.strip()


def requires_registration_enabled(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    """Request requires registration to be enabled.

    Verifies that user registration is enabled in the application settings.

    Args:
        connection (ASGIConnection): HTTP Request
        _ (BaseRouteHandler): Route handler

    Raises:
        PermissionDeniedException: If registration is disabled.
    """
    if get_settings().app.REGISTRATION_ENABLED:
        return
    msg = "Registration is currently disabled."
    raise PermissionDeniedException(detail=msg)


def requires_active_user(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    """Request requires active user.

    Verifies the request user is active.

    Args:
        connection (ASGIConnection): HTTP Request
        _ (BaseRouteHandler): Route handler

    Raises:
        PermissionDeniedException: Permission denied exception
    """
    if connection.user.is_active:
        return
    msg = "Your user account is inactive."
    raise PermissionDeniedException(detail=msg)


def requires_superuser(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    """Request requires active superuser.

    Args:
        connection (ASGIConnection): HTTP Request
        _ (BaseRouteHandler): Route handler

    Raises:
        PermissionDeniedException: Permission denied exception
    """
    if connection.user.is_superuser:
        return
    msg = "Your account does not have enough privileges to access this content."
    raise PermissionDeniedException(detail=msg)


def requires_verified_user(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    """Verify the connection user is a superuser.

    Args:
        connection (ASGIConnection): Request/Connection object.
        _ (BaseRouteHandler): Route handler.

    Raises:
        PermissionDeniedException: Not authorized
    """
    if connection.user.is_verified:
        return
    msg = "Your account has not been verified."
    raise PermissionDeniedException(detail=msg)


async def current_user_from_session(
    session: dict[str, Any], connection: ASGIConnection[Any, Any, Any, Any],
) -> UserModel | None:
    """Lookup current user from server session state.

    Fetches the user information from the database


    Args:
        session (dict[str,Any]): Litestar session dictionary
        connection (ASGIConnection[Any, Any, Any, Any]): ASGI connection.

    Returns:
        User: User record mapped to the JWT identifier
    """

    db_session = alchemy.provide_session(connection.app.state, connection.scope)
    user_provider: AsyncGenerator[UserService, None] = provide_users_service(db_session)
    token_provider: AsyncGenerator[PersonalAccessTokenService, None] = provide_personal_access_token_service(db_session)
    session_provider: AsyncGenerator[UserSessionService, None] = provide_user_session_service(db_session)
    try:
        users_service = await anext(user_provider)

        if (user_id := session.get("user_id")) is not None:
            user = await users_service.get_one_or_none(email=user_id)
            if user and user.is_active:
                _clear_token_auth(connection)
                tracked_session_id = connection.cookies.get(get_settings().app.SESSION_COOKIE_NAME) or connection.get_session_id()
                if tracked_session_id:
                    sessions_service = await anext(session_provider)
                    await sessions_service.track_session(
                        user=user,
                        session_id=tracked_session_id,
                        ip_address=connection.client.host if connection.client else None,
                        user_agent=connection.headers.get("user-agent"),
                    )
                share(connection, "auth", {"isAuthenticated": True, "user": users_service.to_schema(user, schema_type=UserSchema)})
                return user
            session.pop("user_id", None)

        if connection.url.path.startswith("/api/") and (plain_token := _get_bearer_token(connection)):
            token_service = await anext(token_provider)
            token = await token_service.verify_token(plain_token)
            if token is not None:
                user = await users_service.get_one_or_none(id=token.user_id)
                if user and user.is_active:
                    _set_token_auth(connection, token_id=str(token.id), abilities=token.abilities)
                    share(
                        connection,
                        "auth",
                        {"isAuthenticated": True, "user": users_service.to_schema(user, schema_type=UserSchema)},
                    )
                    return user

        _clear_token_auth(connection)
    finally:
        await user_provider.aclose()
        await token_provider.aclose()
        await session_provider.aclose()
    share(connection, "auth", {"isAuthenticated": False})
    return None


session_auth = SessionAuth[UserModel, ServerSideSessionBackend](
    session_backend_config=session_config,
    retrieve_user_handler=current_user_from_session,
    exclude=["^/schema", "^/health", "^/login", "^/register", "^/forgot-password", "^/reset-password", "^/verify-email", "^/mfa-challenge", "^/o/"],
)
github_oauth_callback = OAuth2AuthorizeCallback(
    github_oauth2_client, route_name="github.complete", state_session_key="oauth_state:auth:github",
)
google_oauth_callback = OAuth2AuthorizeCallback(
    google_oauth2_client, route_name="google.complete", state_session_key="oauth_state:auth:google",
)

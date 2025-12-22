from __future__ import annotations

from typing import TYPE_CHECKING, Any

from litestar.exceptions import PermissionDeniedException
from litestar.middleware.session.server_side import ServerSideSessionBackend
from litestar.security.session_auth import SessionAuth
from litestar_vite.inertia import share

from app.config import alchemy, github_oauth2_client, google_oauth2_client
from app.config import session as session_config
from app.db.models import User as UserModel
from app.domain.accounts.dependencies import provide_users_service
from app.domain.accounts.schemas import User as UserSchema
from app.lib.oauth import OAuth2AuthorizeCallback
from app.lib.settings import get_settings

if TYPE_CHECKING:
    from litestar.connection import ASGIConnection
    from litestar.handlers.base import BaseRouteHandler


__all__ = (
    "current_user_from_session",
    "requires_active_user",
    "requires_registration_enabled",
    "requires_superuser",
    "requires_verified_user",
    "session_auth",
)


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

    if (user_id := session.get("user_id")) is None:
        share(connection, "auth", {"isAuthenticated": False})
        return None
    service = await anext(provide_users_service(alchemy.provide_session(connection.app.state, connection.scope)))
    user = await service.get_one_or_none(email=user_id)
    if user and user.is_active:
        share(connection, "auth", {"isAuthenticated": True, "user": service.to_schema(user, schema_type=UserSchema)})
        return user
    share(connection, "auth", {"isAuthenticated": False})
    return None


session_auth = SessionAuth[UserModel, ServerSideSessionBackend](
    session_backend_config=session_config,
    retrieve_user_handler=current_user_from_session,
    exclude=["^/schema", "^/health", "^/login", "^/register", "^/forgot-password", "^/reset-password", "^/verify-email", "^/o/"],
)
github_oauth_callback = OAuth2AuthorizeCallback(github_oauth2_client, route_name="github.complete")
google_oauth_callback = OAuth2AuthorizeCallback(google_oauth2_client, route_name="google.complete")

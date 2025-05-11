from __future__ import annotations

from typing import TYPE_CHECKING

from litestar.exceptions import PermissionDeniedException
from litestar.security.jwt import OAuth2PasswordBearerAuth
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from litestar.exceptions import PermissionDeniedException
from litestar.middleware.session.server_side import ServerSideSessionBackend
from litestar.security.session_auth import SessionAuth
from litestar_vite.inertia import share

from app.config import alchemy, github_oauth2_client, google_oauth2_client
from app.config import session as session_config
from app.db.models import User as UserModel
from app.domain.accounts.deps import provide_users_service
from app.domain.accounts.schemas import User as UserSchema
from app import config
from app.db import models as m
from app.lib import constants 
from app.server import deps
from app.utils.oauth import OAuth2AuthorizeCallback

if TYPE_CHECKING:
    from typing import Any

    from litestar.connection import ASGIConnection, Request
    from litestar.handlers.base import BaseRouteHandler
    from litestar.security.jwt import Token

settings = get_settings()


def provide_user(request: Request[m.User, Token, Any]) -> m.User:
    """Get the user from the connection.

    Args:
        request: current connection.

    Returns:
    User
    """
    return request.user


def requires_active_user(connection: ASGIConnection[Any, m.User, Any, Any], _: BaseRouteHandler) -> None:
    """Request requires active user.

    Verifies the connection user is active.

    Args:
        connection (ASGIConnection): Request/Connection object.
        _ (BaseRouteHandler): Route handler.

    Raises:
        PermissionDeniedException: Not authorized
    """
    if connection.user.is_active:
        return
    msg = "Inactive account"
    raise PermissionDeniedException(msg)


def requires_verified_user(connection: ASGIConnection[Any, m.User, Any, Any], _: BaseRouteHandler) -> None:
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


def requires_superuser(connection: ASGIConnection[Any, m.User, Any, Any], _: BaseRouteHandler) -> None:
    """Verify the connection user is a superuser.

    Args:
        connection (ASGIConnection): Request/Connection object.
        _ (BaseRouteHandler): Route handler.

    Raises:
        PermissionDeniedException: Not authorized
    """
    if connection.user.is_superuser:
        return
    if any(
        assigned_role.role_name
        for assigned_role in connection.user.roles
        if assigned_role.role_name == constants.SUPERUSER_ACCESS_ROLE
    ):
        return
    raise PermissionDeniedException(detail="Insufficient privileges")


def requires_team_membership(connection: ASGIConnection[Any, m.User, Token, Any], _: BaseRouteHandler) -> None:
    """Verify the connection user is a member of the team.

    Args:
        connection (ASGIConnection): Request/Connection object.
        _ (BaseRouteHandler): Route handler.

    Raises:
        PermissionDeniedException: Not authorized

    """
    team_id = connection.path_params["team_id"]
    has_system_role = any(
        assigned_role.role_name
        for assigned_role in connection.user.roles
        if assigned_role.role_name == constants.SUPERUSER_ACCESS_ROLE
    )
    has_team_role = any(membership.team.id == team_id for membership in connection.user.teams)
    if connection.user.is_superuser or has_system_role or has_team_role:
        return
    raise PermissionDeniedException(detail="Insufficient permissions to access team.")


def requires_team_admin(connection: ASGIConnection[Any, m.User, Token, Any], _: BaseRouteHandler) -> None:
    """Verify the connection user is a team admin.

    Args:
        connection (ASGIConnection): Request/Connection object.
        _ (BaseRouteHandler): Route handler.

    Raises:
        PermissionDeniedException: Not authorized

    """
    team_id = connection.path_params["team_id"]
    has_system_role = any(
        assigned_role.role_name
        for assigned_role in connection.user.roles
        if assigned_role.role_name == constants.SUPERUSER_ACCESS_ROLE
    )
    has_team_role = any(
        membership.team.id == team_id and membership.role == m.TeamRoles.ADMIN for membership in connection.user.teams
    )
    if connection.user.is_superuser or has_system_role or has_team_role:
        return
    raise PermissionDeniedException(detail="Insufficient permissions to access team.")


def requires_team_ownership(connection: ASGIConnection[Any, m.User, Token, Any], _: BaseRouteHandler) -> None:
    """Verify that the connection user is the team owner.

    Args:
        connection (ASGIConnection): Request/Connection object.
        _ (BaseRouteHandler): Route handler.

    Raises:
        PermissionDeniedException: Not authorized

    """
    team_id = connection.path_params["team_id"]
    has_system_role = any(
        assigned_role.role_name
        for assigned_role in connection.user.roles
        if assigned_role.role_name == constants.SUPERUSER_ACCESS_ROLE
    )
    has_team_role = any(membership.team.id == team_id and membership.is_owner for membership in connection.user.teams)
    if connection.user.is_superuser or has_system_role or has_team_role:
        return

    msg = "Insufficient permissions to access team."
    raise PermissionDeniedException(msg)


async def current_user_from_session(
    session: dict[str, Any],
    connection: ASGIConnection[Any, Any, Any, Any],
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


session_auth = SessionAuth[m.User, ServerSideSessionBackend](
    session_backend_config=session_config,
    retrieve_user_handler=current_user_from_session,
    exclude=[
        "^/schema",
        "^/health",
        "^/login",
        "^/register",
        "^/o/",
    ],
)
github_oauth_callback = OAuth2AuthorizeCallback(github_oauth2_client, route_name="github.complete")
google_oauth_callback = OAuth2AuthorizeCallback(google_oauth2_client, route_name="google.complete")

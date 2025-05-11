"""User Account Controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from advanced_alchemy.extensions.litestar.providers import create_service_provider
from sqlalchemy.orm import joinedload, load_only, selectinload

from app.db import models as m
from app.domain.accounts.services import UserService

if TYPE_CHECKING:
    from litestar import Request

# create a hard reference to this since it's used oven
provide_users_service = create_service_provider(
    UserService,
    load=[
        selectinload(m.User.roles).options(joinedload(m.UserRole.role, innerjoin=True)),
        selectinload(m.User.teams).options(
            joinedload(m.TeamMember.team, innerjoin=True).options(load_only(m.Team.name)),
        ),
    ],
    error_messages={
        "duplicate_key": "A user with this email already exists",
        "foreign_key": "A user with this email already exists",
        "integrity": "User operation failed.",
    },
)


def provide_user(request: Request[m.User, Any, Any]) -> m.User:
    """Get the user from the request.

    Args:
        request: current Request.

    Returns:
        User
    """
    return request.user

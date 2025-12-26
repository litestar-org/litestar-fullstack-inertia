"""User Account Dependencies."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from advanced_alchemy.extensions.litestar.providers import create_service_provider
from sqlalchemy.orm import joinedload, load_only, selectinload

from app.db.models import Role, Team, TeamMember, UserOauthAccount, UserRole
from app.db.models import User as UserModel
from app.domain.accounts.services import (
    EmailTokenService,
    RoleService,
    UserOAuthAccountService,
    UserRoleService,
    UserService,
)

if TYPE_CHECKING:
    from litestar.connection import Request


def provide_user(request: Request[UserModel, Any, Any]) -> UserModel:
    """Get the user from the connection.

    Args:
        request: current connection.

    Returns:
        User
    """
    return request.user


provide_users_service = create_service_provider(
    UserService,
    load=[
        selectinload(UserModel.roles).options(joinedload(UserRole.role, innerjoin=True)),
        selectinload(UserModel.oauth_accounts),
        selectinload(UserModel.teams).options(
            joinedload(TeamMember.team, innerjoin=True).options(load_only(Team.name, Team.slug)),
        ),
    ],
    error_messages={
        "duplicate_key": "A user with this email already exists",
        "foreign_key": "A user with this email already exists",
        "integrity": "User operation failed.",
    },
)

provide_roles_service = create_service_provider(
    RoleService, load=[selectinload(Role.users).options(joinedload(UserRole.user, innerjoin=True))],
)

provide_user_oauth_account_service = create_service_provider(UserOAuthAccountService, load=[UserOauthAccount.user])

provide_user_roles_service = create_service_provider(UserRoleService)

provide_email_token_service = create_service_provider(EmailTokenService)

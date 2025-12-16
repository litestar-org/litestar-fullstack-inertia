from __future__ import annotations

from advanced_alchemy.repository import SQLAlchemyAsyncRepository, SQLAlchemyAsyncSlugRepository

from app.db.models import EmailToken, Role, User, UserOauthAccount, UserRole


class UserRepository(SQLAlchemyAsyncRepository[User]):
    """User SQLAlchemy Repository."""

    model_type = User


class UserOauthAccountRepository(SQLAlchemyAsyncRepository[UserOauthAccount]):
    """User SQLAlchemy Repository."""

    model_type = UserOauthAccount


class RoleRepository(SQLAlchemyAsyncSlugRepository[Role]):
    """User SQLAlchemy Repository."""

    model_type = Role


class UserRoleRepository(SQLAlchemyAsyncRepository[UserRole]):
    """User Role SQLAlchemy Repository."""

    model_type = UserRole


class EmailTokenRepository(SQLAlchemyAsyncRepository[EmailToken]):
    """Repository for email token operations."""

    model_type = EmailToken

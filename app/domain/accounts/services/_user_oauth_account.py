from __future__ import annotations

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

from app.db.models import UserOauthAccount


class UserOAuthAccountService(SQLAlchemyAsyncRepositoryService[UserOauthAccount]):
    """Handles database operations for user OAuth accounts."""

    class Repo(SQLAlchemyAsyncRepository[UserOauthAccount]):
        """User OAuth Account SQLAlchemy Repository."""

        model_type = UserOauthAccount

    repository_type = Repo

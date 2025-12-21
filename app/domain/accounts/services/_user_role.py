from __future__ import annotations

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

from app.db.models import UserRole


class UserRoleService(SQLAlchemyAsyncRepositoryService[UserRole]):
    """Handles database operations for user roles."""

    class Repo(SQLAlchemyAsyncRepository[UserRole]):
        """User Role SQLAlchemy Repository."""

        model_type = UserRole

    repository_type = Repo

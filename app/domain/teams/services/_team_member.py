from __future__ import annotations

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

from app.db.models import TeamMember

__all__ = ("TeamMemberService",)


class TeamMemberService(SQLAlchemyAsyncRepositoryService[TeamMember]):
    """Team Member Service."""

    class Repo(SQLAlchemyAsyncRepository[TeamMember]):
        """Team Member SQLAlchemy Repository."""

        model_type = TeamMember

    repository_type = Repo

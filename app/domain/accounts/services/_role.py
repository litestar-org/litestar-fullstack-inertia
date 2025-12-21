from __future__ import annotations

from advanced_alchemy.repository import SQLAlchemyAsyncSlugRepository
from advanced_alchemy.service import (
    ModelDictT,
    SQLAlchemyAsyncRepositoryService,
    is_dict_with_field,
    is_dict_without_field,
    schema_dump,
)

from app.db.models import Role


class RoleService(SQLAlchemyAsyncRepositoryService[Role]):
    """Handles database operations for roles."""

    class Repo(SQLAlchemyAsyncSlugRepository[Role]):
        """Role SQLAlchemy Repository."""

        model_type = Role

    repository_type = Repo
    match_fields = ["name"]

    async def to_model_on_create(self, data: ModelDictT[Role]) -> ModelDictT[Role]:
        """Auto-generate slug on create if not provided.

        Returns:
            Role data with auto-generated slug if not provided.
        """
        data = schema_dump(data)
        if is_dict_without_field(data, "slug"):
            data["slug"] = await self.repository.get_available_slug(data["name"])
        return data

    async def to_model_on_update(self, data: ModelDictT[Role]) -> ModelDictT[Role]:
        """Auto-generate slug on update if name changed but no slug provided.

        Returns:
            Role data with auto-generated slug if name changed without slug.
        """
        data = schema_dump(data)
        if is_dict_without_field(data, "slug") and is_dict_with_field(data, "name"):
            data["slug"] = await self.repository.get_available_slug(data["name"])
        return data

from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.service import (
    SQLAlchemyAsyncRepositoryService,
    is_dict_with_field,
    is_dict_without_field,
    schema_dump,
)
from advanced_alchemy.utils.text import slugify

from app.db.models import Tag

from .repositories import TagRepository

if TYPE_CHECKING:
    from advanced_alchemy.service import ModelDictT

__all__ = ("TagService",)


class TagService(SQLAlchemyAsyncRepositoryService[Tag, TagRepository]):
    """Handles basic lookup operations for a Tag."""

    repository_type = TagRepository
    match_fields = ["name"]

    async def to_model_on_create(self, data: ModelDictT[Tag]) -> ModelDictT[Tag]:
        """Auto-generate slug from name if not provided.

        Returns:
            Tag data with auto-generated slug.
        """
        data = schema_dump(data)
        if is_dict_without_field(data, "slug") and is_dict_with_field(data, "name"):
            data["slug"] = slugify(data["name"])
        return data

    async def to_model_on_update(self, data: ModelDictT[Tag]) -> ModelDictT[Tag]:
        """Update slug when name changes.

        Returns:
            Tag data with updated slug if name changed.
        """
        data = schema_dump(data)
        if is_dict_without_field(data, "slug") and is_dict_with_field(data, "name"):
            data["slug"] = slugify(data["name"])
        return data

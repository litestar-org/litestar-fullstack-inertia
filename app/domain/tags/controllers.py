"""Tag Controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from advanced_alchemy.extensions.litestar.providers import create_service_dependencies
from litestar import Controller, delete, get, patch, post
from litestar.params import Dependency, Parameter

from app.db.models import Tag as TagModel
from app.domain.accounts.guards import requires_active_user, requires_superuser
from app.domain.tags.schemas import Tag, TagCreate, TagUpdate
from app.domain.tags.services import TagService

if TYPE_CHECKING:
    from advanced_alchemy.filters import FilterTypes
    from advanced_alchemy.service import OffsetPagination


class TagController(Controller):
    """Handles the interactions within the Tag objects."""

    guards = [requires_active_user]
    dependencies = create_service_dependencies(
        TagService,
        key="tags_service",
        load=[TagModel.teams],
        filters={
            "id_filter": UUID,
            "created_at": True,
            "updated_at": True,
            "sort_field": "name",
            "search": "name,slug",
            "pagination_type": "limit_offset",
            "pagination_size": 20,
        },
    )
    signature_namespace = {"TagService": TagService, "TagCreate": TagCreate, "TagUpdate": TagUpdate}
    tags = ["Tags"]

    @get(
        operation_id="ListTags",
        name="tags:list",
        summary="List Tags",
        description="Retrieve the tags.",
        path="/api/tags",
    )
    async def list_tags(
        self,
        tags_service: TagService,
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> OffsetPagination[Tag]:
        """List tags.

        Returns:
            Paginated list of tags.
        """
        results, total = await tags_service.list_and_count(*filters)
        return tags_service.to_schema(schema_type=Tag, data=results, total=total, filters=filters)

    @get(
        operation_id="GetTag",
        name="tags:get",
        path="/api/tags/{tag_id:uuid}",
        summary="Retrieve the details of a tag.",
    )
    async def get_tag(
        self,
        tags_service: TagService,
        tag_id: Annotated[UUID, Parameter(title="Tag ID", description="The tag to retrieve.")],
    ) -> Tag:
        """Get a tag.

        Returns:
            Tag data for the requested tag.
        """
        db_obj = await tags_service.get(tag_id)
        return tags_service.to_schema(schema_type=Tag, data=db_obj)

    @post(
        operation_id="CreateTag",
        name="tags:create",
        summary="Create a new tag.",
        cache_control=None,
        description="A tag is a place where you can upload and group collections of databases.",
        guards=[requires_superuser],
        path="/api/tags",
    )
    async def create_tag(
        self,
        tags_service: TagService,
        data: TagCreate,
    ) -> Tag:
        """Create a new tag.

        Returns:
            Newly created tag data.
        """
        db_obj = await tags_service.create(data.to_dict())
        return tags_service.to_schema(schema_type=Tag, data=db_obj)

    @patch(
        operation_id="UpdateTag",
        name="tags:update",
        path="/api/tags/{tag_id:uuid}",
        guards=[requires_superuser],
    )
    async def update_tag(
        self,
        tags_service: TagService,
        data: TagUpdate,
        tag_id: Annotated[UUID, Parameter(title="Tag ID", description="The tag to update.")],
    ) -> Tag:
        """Update a tag.

        Returns:
            Updated tag data.
        """
        db_obj = await tags_service.update(item_id=tag_id, data=data.to_dict())
        return tags_service.to_schema(schema_type=Tag, data=db_obj)

    @delete(
        operation_id="DeleteTag",
        name="tags:delete",
        path="/api/tags/{tag_id:uuid}",
        summary="Remove Tag",
        description="Removes a tag and its associations",
        guards=[requires_superuser],
    )
    async def delete_tag(
        self,
        tags_service: TagService,
        tag_id: Annotated[UUID, Parameter(title="Tag ID", description="The tag to delete.")],
    ) -> None:
        """Delete a tag."""
        _ = await tags_service.delete(tag_id)

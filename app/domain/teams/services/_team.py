from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.exceptions import RepositoryError
from advanced_alchemy.repository import SQLAlchemyAsyncSlugRepository
from advanced_alchemy.service import (
    SQLAlchemyAsyncRepositoryService,
    is_dict,
    is_dict_with_field,
    is_dict_without_field,
    schema_dump,
)
from advanced_alchemy.utils.text import slugify
from uuid_utils import uuid7

from app.db.models import Team, TeamMember, TeamRoles
from app.db.models.tag import Tag
from app.db.models.user import User  # noqa: TC001

if TYPE_CHECKING:
    from uuid import UUID

    from advanced_alchemy.service import ModelDictT

__all__ = ("TeamService",)


class TeamService(SQLAlchemyAsyncRepositoryService[Team]):
    """Team Service."""

    class Repo(SQLAlchemyAsyncSlugRepository[Team]):
        """Team SQLAlchemy Repository."""

        model_type = Team

    repository_type = Repo
    match_fields = ["name"]

    async def to_model_on_create(self, data: ModelDictT[Team]) -> ModelDictT[Team]:
        """Transform data before creating a team with slug, owner, and tags.

        Returns:
            Transformed team data with slug, owner member, and tags populated.
        """
        return await self._populate_with_owner_and_tags(await self._populate_slug(schema_dump(data)), "create")

    async def to_model_on_update(self, data: ModelDictT[Team]) -> ModelDictT[Team]:
        """Transform data before updating a team with slug and tags if provided.

        Returns:
            Transformed team data with slug and tags updated.
        """
        return await self._populate_with_owner_and_tags(await self._populate_slug(schema_dump(data)), "update")

    async def _populate_slug(self, data: ModelDictT[Team]) -> ModelDictT[Team]:
        """Auto-generate slug from name if not provided.

        Returns:
            Team data with auto-generated slug if name provided without slug.
        """
        if is_dict_without_field(data, "slug") and is_dict_with_field(data, "name"):
            data["slug"] = await self.repository.get_available_slug(data["name"])
        return data

    async def _populate_with_owner_and_tags(self, data: ModelDictT[Team], operation: str) -> ModelDictT[Team]:
        """Handle owner and tags assignment.

        Returns:
            Team data with owner member and tags populated.

        Raises:
            RepositoryError: If owner_id is not provided on create.
        """
        if not is_dict(data):
            return data

        owner_id: UUID | None = data.pop("owner_id", None)
        owner: User | None = data.pop("owner", None)
        input_tags: list[str] = data.pop("tags", [])

        if operation == "create":
            if "id" not in data:
                data["id"] = uuid7()
            if owner_id is None and owner is None:
                msg = "'owner_id' is required to create a team."
                raise RepositoryError(msg)

        data = await super().to_model(data)

        if operation == "create":
            data.members.append(
                TeamMember(user=owner, role=TeamRoles.ADMIN, is_owner=True)
                if owner
                else TeamMember(user_id=owner_id, role=TeamRoles.ADMIN, is_owner=True),
            )

        if input_tags:
            existing = {tag.name for tag in data.tags}
            for tag in [t for t in data.tags if t.name not in input_tags]:
                data.tags.remove(tag)
            data.tags.extend([
                await Tag.as_unique_async(self.repository.session, name=name, slug=slugify(name))
                for name in input_tags
                if name not in existing
            ])

        return data

    @staticmethod
    def can_view_all(user: User) -> bool:
        """Check if user can view all teams.

        Returns:
            True if user is superuser, False otherwise.
        """
        return bool(
            user.is_superuser
            or any(assigned_role.role.name for assigned_role in user.roles if assigned_role.role.name in {"Superuser"}),
        )

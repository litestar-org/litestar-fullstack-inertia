from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.exceptions import RepositoryError
from advanced_alchemy.service import (
    SQLAlchemyAsyncRepositoryService,
    is_dict,
    is_dict_with_field,
    is_dict_without_field,
    schema_dump,
)
from advanced_alchemy.utils.text import slugify
from uuid_utils.compat import uuid4

from app.db.models import Team, TeamInvitation, TeamMember, TeamRoles
from app.db.models.tag import Tag
from app.db.models.user import User  # noqa: TC001
from app.domain.teams.repositories import TeamInvitationRepository, TeamMemberRepository, TeamRepository

if TYPE_CHECKING:
    from uuid import UUID

    from advanced_alchemy.service import ModelDictT

__all__ = (
    "TeamInvitationService",
    "TeamMemberService",
    "TeamService",
)


class TeamService(SQLAlchemyAsyncRepositoryService[Team]):
    """Team Service."""

    repository_type = TeamRepository
    match_fields = ["name"]

    async def to_model_on_create(self, data: ModelDictT[Team]) -> ModelDictT[Team]:
        """Transform data before creating a team."""
        data = schema_dump(data)
        data = await self._populate_slug(data)
        return await self._populate_with_owner_and_tags(data, "create")

    async def to_model_on_update(self, data: ModelDictT[Team]) -> ModelDictT[Team]:
        """Transform data before updating a team."""
        data = schema_dump(data)
        data = await self._populate_slug(data)
        return await self._populate_with_owner_and_tags(data, "update")

    async def _populate_slug(self, data: ModelDictT[Team]) -> ModelDictT[Team]:
        """Auto-generate slug if not provided."""
        if is_dict_without_field(data, "slug") and is_dict_with_field(data, "name"):
            data["slug"] = await self.repository.get_available_slug(data["name"])
        return data

    async def _populate_with_owner_and_tags(
        self,
        data: ModelDictT[Team],
        operation: str,
    ) -> ModelDictT[Team]:
        """Handle owner and tags assignment.

        Raises:
            RepositoryError: If owner_id is not provided on create.
        """
        if not is_dict(data):
            return data

        # Extract and remove owner/tags from input
        owner_id: UUID | None = data.pop("owner_id", None)
        owner: User | None = data.pop("owner", None)
        input_tags: list[str] = data.pop("tags", [])

        # Set ID if not provided (only on create)
        if operation == "create" and "id" not in data:
            data["id"] = uuid4()

        # Validate owner on create
        if operation == "create" and owner_id is None and owner is None:
            msg = "'owner_id' is required to create a team."
            raise RepositoryError(msg)

        # Convert to model
        data = await super().to_model(data)

        # Handle owner on create
        if operation == "create":
            if owner:
                data.members.append(TeamMember(user=owner, role=TeamRoles.ADMIN, is_owner=True))
            elif owner_id:
                data.members.append(TeamMember(user_id=owner_id, role=TeamRoles.ADMIN, is_owner=True))

        # Handle tags
        if input_tags:
            existing_tags = [tag.name for tag in data.tags]
            tags_to_remove = [tag for tag in data.tags if tag.name not in input_tags]
            tags_to_add = [tag for tag in input_tags if tag not in existing_tags]

            for tag_rm in tags_to_remove:
                data.tags.remove(tag_rm)

            data.tags.extend(
                [
                    await Tag.as_unique_async(self.repository.session, name=tag_text, slug=slugify(tag_text))
                    for tag_text in tags_to_add
                ],
            )

        return data

    @staticmethod
    def can_view_all(user: User) -> bool:
        return bool(
            user.is_superuser
            or any(assigned_role.role.name for assigned_role in user.roles if assigned_role.role.name in {"Superuser"}),
        )


class TeamMemberService(SQLAlchemyAsyncRepositoryService[TeamMember]):
    """Team Member Service."""

    repository_type = TeamMemberRepository


class TeamInvitationService(SQLAlchemyAsyncRepositoryService[TeamInvitation]):
    """Team Invitation Service."""

    repository_type = TeamInvitationRepository

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
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
from sqlalchemy import ColumnElement, or_
from uuid_utils.compat import uuid4

from app.db.models import Team, TeamInvitation, TeamMember, TeamRoles
from app.db.models.tag import Tag
from app.db.models.user import User  # noqa: TC001
from app.domain.teams.repositories import TeamInvitationRepository, TeamMemberRepository, TeamRepository
from app.lib.settings import get_settings

if TYPE_CHECKING:
    from uuid import UUID

    from advanced_alchemy.service import ModelDictT

__all__ = ("TeamInvitationService", "TeamMemberService", "TeamService")


class TeamService(SQLAlchemyAsyncRepositoryService[Team, TeamRepository]):
    """Team Service."""

    repository_type = TeamRepository
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
                data["id"] = uuid4()
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


class TeamMemberService(SQLAlchemyAsyncRepositoryService[TeamMember, TeamMemberRepository]):
    """Team Member Service."""

    repository_type = TeamMemberRepository


class TeamInvitationService(SQLAlchemyAsyncRepositoryService[TeamInvitation, TeamInvitationRepository]):
    """Team Invitation Service."""

    repository_type = TeamInvitationRepository

    @staticmethod
    def _hash_token(token: str) -> str:
        """Hash a token using SHA-256.

        Returns:
            Hexadecimal digest of the hashed token.
        """
        return hashlib.sha256(token.encode()).hexdigest()

    def _not_expired_filter(self) -> ColumnElement[bool]:
        """SQLAlchemy filter for non-expired invitations.

        Returns:
            Column expression filtering for invitations with no expiry or future expiry.
        """
        return or_(TeamInvitation.expires_at.is_(None), TeamInvitation.expires_at > datetime.now(UTC))

    async def to_model_on_create(self, data: ModelDictT[TeamInvitation]) -> ModelDictT[TeamInvitation]:
        """Set defaults for new invitations.

        Handles token hashing (if plain token provided) and default expiry.

        Returns:
            Invitation data with hashed token and expiry set.
        """
        data = schema_dump(data)
        if is_dict_with_field(data, "token") and is_dict_without_field(data, "token_hash"):
            data["token_hash"] = self._hash_token(data.pop("token"))
        if is_dict_without_field(data, "expires_at"):
            data["expires_at"] = datetime.now(UTC) + timedelta(days=get_settings().email.INVITATION_TOKEN_EXPIRES_DAYS)
        return data

    async def create_invitation(
        self, team: Team, email: str, role: TeamRoles, invited_by: User,
    ) -> tuple[TeamInvitation, str]:
        """Create a new team invitation.

        Returns:
            Tuple of (invitation record, plain token for email).
        """
        token = secrets.token_urlsafe(32)
        invitation = await self.create({
            "team_id": team.id,
            "email": email,
            "role": role,
            "invited_by_id": invited_by.id,
            "invited_by_email": invited_by.email,
            "token": token,  # to_model_on_create hashes this
        })
        return invitation, token

    async def get_by_token(self, token: str) -> TeamInvitation | None:
        """Find an invitation by its plain token.

        Returns:
            TeamInvitation if found, None otherwise.
        """
        return await self.get_one_or_none(token_hash=self._hash_token(token))

    async def get_pending_for_team(self, team_id: UUID) -> list[TeamInvitation]:
        """Get all pending (not accepted, not expired) invitations for a team.

        Returns:
            List of pending invitations for the team.
        """
        return list(
            await self.list(
                self._not_expired_filter(), TeamInvitation.team_id == team_id, TeamInvitation.is_accepted.is_(False),
            ),
        )

    async def get_pending_for_email(self, email: str) -> list[TeamInvitation]:
        """Get all pending invitations for an email address.

        Returns:
            List of pending invitations for the email.
        """
        return list(
            await self.list(
                self._not_expired_filter(), TeamInvitation.email == email, TeamInvitation.is_accepted.is_(False),
            ),
        )

    async def accept_invitation(
        self, invitation: TeamInvitation, user: User, team_member_service: "TeamMemberService",
    ) -> TeamMember:
        """Accept an invitation and create a team member.

        Returns:
            The created TeamMember.

        Raises:
            RepositoryError: If invitation is expired or already accepted.
        """
        if invitation.is_expired:
            msg = "This invitation has expired."
            raise RepositoryError(msg)
        if invitation.is_accepted:
            msg = "This invitation has already been accepted."
            raise RepositoryError(msg)

        team_member = await team_member_service.create({
            "team_id": invitation.team_id,
            "user_id": user.id,
            "role": invitation.role,
            "is_owner": False,
        })
        invitation.is_accepted = True
        invitation.accepted_at = datetime.now(UTC)
        await self.update(item_id=invitation.id, data=invitation)
        return team_member

    async def has_pending_invitation(self, team_id: UUID, email: str) -> bool:
        """Check if there's already a pending invitation for this email on this team.

        Returns:
            True if a pending invitation exists, False otherwise.
        """
        return await self.exists(
            self._not_expired_filter(),
            TeamInvitation.team_id == team_id,
            TeamInvitation.email == email,
            TeamInvitation.is_accepted.is_(False),
        )

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from uuid import UUID  # noqa: TC003

import msgspec

from app.db.models.team_roles import TeamRoles
from app.lib.schema import CamelizedBaseStruct


class TeamTag(CamelizedBaseStruct):
    id: UUID
    slug: str
    name: str


class TeamMember(CamelizedBaseStruct):
    id: UUID
    user_id: UUID
    email: str
    name: str | None = None
    role: TeamRoles | None = TeamRoles.MEMBER
    is_owner: bool | None = False


class Team(CamelizedBaseStruct):
    id: UUID
    name: str
    description: str | None = None
    members: list[TeamMember] = []
    tags: list[TeamTag] = []


class TeamCreate(CamelizedBaseStruct):
    name: str
    description: str | None = None
    tags: list[str] = []


class TeamUpdate(CamelizedBaseStruct, omit_defaults=True):
    name: str | None | msgspec.UnsetType = msgspec.UNSET
    description: str | None | msgspec.UnsetType = msgspec.UNSET
    tags: list[str] | None | msgspec.UnsetType = msgspec.UNSET


class TeamMemberModify(CamelizedBaseStruct):
    """Team Member Modify."""

    user_name: str


class CurrentTeam(CamelizedBaseStruct):
    """Current team stored in session."""

    team_id: UUID
    team_name: str


# Page response schemas for Inertia pages


class TeamListItem(CamelizedBaseStruct):
    """Team item in list view."""

    id: UUID
    name: str
    slug: str
    member_count: int
    user_role: str
    description: str | None = None
    created_at: datetime | None = None


class TeamListPage(CamelizedBaseStruct):
    """Response for team list page."""

    teams: list[TeamListItem]
    total: int


class TeamPageMember(CamelizedBaseStruct):
    """Team member for page display (includes avatar)."""

    id: UUID
    user_id: UUID
    email: str
    role: str
    name: str | None = None
    avatar_url: str | None = None


class TeamPermissions(CamelizedBaseStruct):
    """User permissions for team management."""

    can_add_team_members: bool
    can_delete_team: bool
    can_remove_team_members: bool
    can_update_team: bool


class TeamDetail(CamelizedBaseStruct):
    """Team details for show/settings page."""

    id: UUID
    name: str
    slug: str
    description: str | None = None
    created_at: datetime | None = None


class TeamDetailPage(CamelizedBaseStruct):
    """Response for team show/settings page."""

    team: TeamDetail
    members: list[TeamPageMember]
    permissions: TeamPermissions

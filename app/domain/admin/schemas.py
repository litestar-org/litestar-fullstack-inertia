"""Admin domain schemas."""
# ruff: noqa: TC003

from __future__ import annotations

from datetime import datetime
from uuid import UUID

import msgspec

from app.db.models.team_roles import TeamRoles
from app.lib.schema import CamelizedBaseStruct

__all__ = (
    "AdminDashboardPage",
    "AdminStats",
    "AdminTeamDetail",
    "AdminTeamDetailPage",
    "AdminTeamListItem",
    "AdminTeamListPage",
    "AdminTeamMemberAdd",
    "AdminTeamUpdate",
    "AdminUserCreate",
    "AdminUserDetail",
    "AdminUserDetailPage",
    "AdminUserListItem",
    "AdminUserListPage",
    "AdminUserRoleAssign",
    "AdminUserUpdate",
    "AuditLogItem",
    "AuditLogPage",
    "RoleOption",
    "TeamMemberInfo",
    "UserRoleInfo",
    "UserTeamInfo",
)


# Role option for dropdowns
class RoleOption(CamelizedBaseStruct):
    """Role option for dropdown selection."""

    id: UUID
    slug: str
    name: str


# User schemas
class UserRoleInfo(CamelizedBaseStruct):
    """Role information for user detail."""

    id: UUID
    role_id: UUID
    role_slug: str
    role_name: str
    assigned_at: datetime


class UserTeamInfo(CamelizedBaseStruct):
    """Team membership information for user detail."""

    team_id: UUID
    team_name: str
    team_slug: str
    role: TeamRoles = TeamRoles.MEMBER
    is_owner: bool = False


class AdminUserListItem(CamelizedBaseStruct):
    """User item for admin list view."""

    id: UUID
    email: str
    name: str | None = None
    is_active: bool = False
    is_superuser: bool = False
    is_verified: bool = False
    is_two_factor_enabled: bool = False
    role_names: list[str] = msgspec.field(default_factory=list)
    team_count: int = 0
    created_at: datetime | None = None
    avatar_url: str | None = None


class AdminUserListPage(CamelizedBaseStruct):
    """Users list page props."""

    users: list[AdminUserListItem]
    total: int
    page: int = 1
    page_size: int = 25
    roles: list[RoleOption] = msgspec.field(default_factory=list)


class AdminUserDetail(CamelizedBaseStruct):
    """Detailed user view for admin."""

    id: UUID
    email: str
    name: str | None = None
    is_active: bool = False
    is_superuser: bool = False
    is_verified: bool = False
    is_two_factor_enabled: bool = False
    has_password: bool = False
    roles: list[UserRoleInfo] = msgspec.field(default_factory=list)
    teams: list[UserTeamInfo] = msgspec.field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    avatar_url: str | None = None


class AdminUserDetailPage(CamelizedBaseStruct):
    """User detail page props."""

    user: AdminUserDetail
    available_roles: list[RoleOption] = msgspec.field(default_factory=list)


class AdminUserCreatePage(CamelizedBaseStruct):
    """User create page props."""

    available_roles: list[RoleOption] = msgspec.field(default_factory=list)


class AdminUserCreate(CamelizedBaseStruct):
    """Create user from admin."""

    email: str
    password: str
    name: str | None = None
    is_superuser: bool = False
    is_active: bool = True
    is_verified: bool = False


class AdminUserUpdate(CamelizedBaseStruct, omit_defaults=True):
    """Update user from admin."""

    email: str | None | msgspec.UnsetType = msgspec.UNSET
    name: str | None | msgspec.UnsetType = msgspec.UNSET
    is_superuser: bool | None | msgspec.UnsetType = msgspec.UNSET
    is_active: bool | None | msgspec.UnsetType = msgspec.UNSET
    is_verified: bool | None | msgspec.UnsetType = msgspec.UNSET


class AdminUserRoleAssign(CamelizedBaseStruct):
    """Assign role to user."""

    role_id: UUID


# Team schemas
class TeamMemberInfo(CamelizedBaseStruct):
    """Team member information."""

    id: UUID
    user_id: UUID
    email: str
    name: str | None = None
    role: TeamRoles = TeamRoles.MEMBER
    is_owner: bool = False
    avatar_url: str | None = None


class AdminTeamListItem(CamelizedBaseStruct):
    """Team item for admin list view."""

    id: UUID
    name: str
    slug: str
    description: str | None = None
    is_active: bool = True
    member_count: int = 0
    owner_email: str | None = None
    created_at: datetime | None = None


class AdminTeamListPage(CamelizedBaseStruct):
    """Teams list page props."""

    teams: list[AdminTeamListItem]
    total: int
    page: int = 1
    page_size: int = 25


class AdminTeamDetail(CamelizedBaseStruct):
    """Detailed team view for admin."""

    id: UUID
    name: str
    slug: str
    description: str | None = None
    is_active: bool = True
    members: list[TeamMemberInfo] = msgspec.field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AdminTeamDetailPage(CamelizedBaseStruct):
    """Team detail page props."""

    team: AdminTeamDetail


class AdminTeamUpdate(CamelizedBaseStruct, omit_defaults=True):
    """Update team from admin."""

    name: str | None | msgspec.UnsetType = msgspec.UNSET
    description: str | None | msgspec.UnsetType = msgspec.UNSET
    is_active: bool | None | msgspec.UnsetType = msgspec.UNSET


class AdminTeamMemberAdd(CamelizedBaseStruct):
    """Add member to team."""

    user_id: UUID
    role: TeamRoles = TeamRoles.MEMBER


# Audit log schemas
class AuditLogItem(CamelizedBaseStruct):
    """Audit log entry."""

    id: UUID
    actor_email: str
    action: str
    target_type: str
    target_id: UUID
    created_at: datetime
    target_label: str | None = None
    details: dict | None = None
    ip_address: str | None = None


class AuditLogPage(CamelizedBaseStruct):
    """Audit log page props."""

    logs: list[AuditLogItem]
    total: int
    page: int = 1
    page_size: int = 50


# Dashboard schemas
class AdminStats(CamelizedBaseStruct):
    """Admin dashboard statistics."""

    total_users: int = 0
    active_users: int = 0
    verified_users: int = 0
    total_teams: int = 0
    recent_signups: int = 0


class AdminDashboardPage(CamelizedBaseStruct):
    """Admin dashboard page props."""

    stats: AdminStats
    recent_logs: list[AuditLogItem] = msgspec.field(default_factory=list)

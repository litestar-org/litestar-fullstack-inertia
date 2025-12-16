from __future__ import annotations

from enum import StrEnum


class TeamRoles(StrEnum):
    """Valid values for team roles.

    Roles follow Jetstream conventions:
    - ADMIN: Full permissions (create, read, update, delete)
    - EDITOR: Limited permissions (read, create, update)
    - MEMBER: Basic read-only access

    Note: Team ownership is tracked separately via is_owner on TeamMember.
    """

    ADMIN = "admin"
    EDITOR = "editor"
    MEMBER = "member"

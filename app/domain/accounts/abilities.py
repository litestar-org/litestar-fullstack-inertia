from __future__ import annotations

from dataclasses import dataclass

__all__ = (
    "DEFAULT_TOKEN_ABILITIES",
    "TOKEN_ABILITY_DEFINITIONS",
    "TOKEN_ABILITY_KEYS",
)


@dataclass(frozen=True, slots=True)
class TokenAbilityDefinition:
    key: str
    label: str
    description: str
    default_enabled: bool = False


TOKEN_ABILITY_DEFINITIONS: tuple[TokenAbilityDefinition, ...] = (
    TokenAbilityDefinition(
        key="tags:read",
        label="Read Tags",
        description="List and view tag records through the API.",
        default_enabled=True,
    ),
    TokenAbilityDefinition(
        key="tags:write",
        label="Manage Tags",
        description="Create, update, and delete tag records through the API.",
    ),
    TokenAbilityDefinition(
        key="teams:write",
        label="Manage Team Members",
        description="Add and remove members on teams you administer.",
    ),
    TokenAbilityDefinition(
        key="users:read",
        label="Read Users",
        description="List and view user records. Superuser checks still apply.",
    ),
    TokenAbilityDefinition(
        key="users:write",
        label="Manage Users",
        description="Create, update, and delete user records. Superuser checks still apply.",
    ),
    TokenAbilityDefinition(
        key="roles:write",
        label="Manage Role Assignments",
        description="Assign and revoke user roles. Superuser checks still apply.",
    ),
)

TOKEN_ABILITY_KEYS = frozenset(definition.key for definition in TOKEN_ABILITY_DEFINITIONS)
DEFAULT_TOKEN_ABILITIES = tuple(
    definition.key for definition in TOKEN_ABILITY_DEFINITIONS if definition.default_enabled
)

from __future__ import annotations

from uuid import UUID  # noqa: TC003

import msgspec

from app.lib.schema import CamelizedBaseStruct

__all__ = ("Tag", "TagCreate", "TagUpdate")


class Tag(CamelizedBaseStruct):
    """Tag response schema."""

    id: UUID
    slug: str
    name: str
    description: str | None = None


class TagCreate(CamelizedBaseStruct):
    """Create a new tag."""

    name: str
    description: str | None = None


class TagUpdate(CamelizedBaseStruct, omit_defaults=True):
    """Update a tag."""

    name: str | None | msgspec.UnsetType = msgspec.UNSET
    description: str | None | msgspec.UnsetType = msgspec.UNSET

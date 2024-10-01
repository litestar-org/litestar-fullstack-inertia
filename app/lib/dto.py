from __future__ import annotations

from typing import TYPE_CHECKING, Literal, overload

from advanced_alchemy.extensions.litestar.dto import SQLAlchemyDTO, SQLAlchemyDTOConfig
from litestar.dto import DataclassDTO, dto_field
from litestar.dto.config import DTOConfig

if TYPE_CHECKING:
    from collections.abc import Set as AbstractSet

    from litestar.dto import RenameStrategy

__all__ = ("config", "dto_field", "DTOConfig", "SQLAlchemyDTO", "DataclassDTO")


@overload
def config(
    backend: Literal["sqlalchemy"] = "sqlalchemy",
    exclude: AbstractSet[str] | None = None,
    rename_fields: dict[str, str] | None = None,
    rename_strategy: RenameStrategy | None = None,
    max_nested_depth: int | None = None,
    partial: bool | None = None,
) -> SQLAlchemyDTOConfig: ...


@overload
def config(
    backend: Literal["dataclass"] = "dataclass",
    exclude: AbstractSet[str] | None = None,
    rename_fields: dict[str, str] | None = None,
    rename_strategy: RenameStrategy | None = None,
    max_nested_depth: int | None = None,
    partial: bool | None = None,
) -> DTOConfig: ...


def config(
    backend: Literal["dataclass", "sqlalchemy"] = "dataclass",
    exclude: AbstractSet[str] | None = None,
    rename_fields: dict[str, str] | None = None,
    rename_strategy: RenameStrategy | None = None,
    max_nested_depth: int | None = None,
    partial: bool | None = None,
) -> DTOConfig | SQLAlchemyDTOConfig:
    """_summary_

    Returns:
        DTOConfig: Configured DTO class
    """
    default_kwargs = {"rename_strategy": "camel", "max_nested_depth": 2}
    if exclude:
        default_kwargs["exclude"] = exclude
    if rename_fields:
        default_kwargs["rename_fields"] = rename_fields
    if rename_strategy:
        default_kwargs["rename_strategy"] = rename_strategy
    if max_nested_depth:
        default_kwargs["max_nested_depth"] = max_nested_depth
    if partial:
        default_kwargs["partial"] = partial
    if backend == "sqlalchemy":
        return SQLAlchemyDTOConfig(**default_kwargs)  # type: ignore[arg-type]
    return DTOConfig(**default_kwargs)  # type: ignore[arg-type]

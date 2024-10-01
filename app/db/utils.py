from __future__ import annotations


async def load_database_fixtures() -> None:
    """Import/Synchronize Database Fixtures."""

    from pathlib import Path

    from advanced_alchemy.utils.fixtures import open_fixture_async
    from sqlalchemy import select
    from sqlalchemy.orm import load_only
    from structlog import get_logger

    from app.config import alchemy
    from app.db.models import Role
    from app.domain.accounts.services import RoleService
    from app.lib.settings import get_settings

    settings = get_settings()
    logger = get_logger()
    fixtures_path = Path(settings.db.FIXTURE_PATH)
    async with RoleService.new(
        statement=select(Role).options(load_only(Role.id, Role.slug, Role.name, Role.description)),
        config=alchemy,
    ) as service:
        fixture_data = await open_fixture_async(fixtures_path, "role")
        await service.upsert_many(match_fields=["name"], data=fixture_data, auto_commit=True)
        await logger.ainfo("loaded roles")

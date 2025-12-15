from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from app.lib import settings as base

if TYPE_CHECKING:
    from pytest import MonkeyPatch


pytestmark = pytest.mark.anyio
pytest_plugins = [
    "tests.data_fixtures",
    "pytest_databases.docker",
    "pytest_databases.docker.postgres",
]


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(autouse=True)
def _patch_settings(monkeypatch: MonkeyPatch) -> None:
    """Path the settings."""

    settings = base.Settings.from_env(".env.testing")

    def get_settings(dotenv_filename: str = ".env.testing") -> base.Settings:
        return settings

    monkeypatch.setattr(base, "get_settings", get_settings)

    # Patch the Vite config dev_mode directly since config.py is loaded before tests
    from app import config
    from app.server import plugins

    monkeypatch.setattr(config.vite, "dev_mode", False)
    monkeypatch.setattr(config.vite.runtime, "dev_mode", False)
    # Also patch the plugin's config
    monkeypatch.setattr(plugins.vite._config, "dev_mode", False)
    monkeypatch.setattr(plugins.vite._config.runtime, "dev_mode", False)

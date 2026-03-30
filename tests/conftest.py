from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from app import config
from app.lib import settings as base
from app.server import plugins

if TYPE_CHECKING:
    from pathlib import Path

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
def _patch_settings(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    """Patch settings and Vite runtime config for tests."""

    settings = base.Settings.from_env(".env.testing")
    settings.storage.UPLOAD_DIR = tmp_path / "uploads"
    settings.storage.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    def get_settings(dotenv_filename: str = ".env.testing") -> base.Settings:
        return settings

    monkeypatch.setattr(base, "get_settings", get_settings)

    # Patch the Vite config dev_mode directly since config.py is loaded before tests
    monkeypatch.setattr(config.vite, "dev_mode", False)
    monkeypatch.setattr(config.vite.runtime, "dev_mode", False)
    # Also patch the plugin's config
    monkeypatch.setattr(plugins.vite._config, "dev_mode", False)
    monkeypatch.setattr(plugins.vite._config.runtime, "dev_mode", False)

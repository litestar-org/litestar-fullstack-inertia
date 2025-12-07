from __future__ import annotations

import binascii
import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Final

from advanced_alchemy.utils.text import slugify
from litestar.utils.module_loader import module_to_os_path
from sqlalchemy.ext.asyncio import AsyncEngine

from app.utils.env import get_env

if TYPE_CHECKING:
    from litestar.data_extractors import RequestExtractorField, ResponseExtractorField

DEFAULT_MODULE_NAME = "app"
BASE_DIR: Final[Path] = module_to_os_path(DEFAULT_MODULE_NAME)


@dataclass
class DatabaseSettings:
    """Database configuration settings."""

    ECHO: bool = field(default_factory=get_env("DATABASE_ECHO", False))
    """Enable SQLAlchemy engine logs."""
    ECHO_POOL: bool = field(default_factory=get_env("DATABASE_ECHO_POOL", False))
    """Enable SQLAlchemy connection pool logs."""
    POOL_DISABLED: bool = field(default_factory=get_env("DATABASE_POOL_DISABLED", False))
    """Disable SQLAlchemy pool configuration."""
    POOL_MAX_OVERFLOW: int = field(default_factory=get_env("DATABASE_MAX_POOL_OVERFLOW", 10))
    """Max overflow for SQLAlchemy connection pool"""
    POOL_SIZE: int = field(default_factory=get_env("DATABASE_POOL_SIZE", 5))
    """Pool size for SQLAlchemy connection pool"""
    POOL_TIMEOUT: int = field(default_factory=get_env("DATABASE_POOL_TIMEOUT", 30))
    """Time in seconds for timing connections out of the connection pool."""
    POOL_RECYCLE: int = field(default_factory=get_env("DATABASE_POOL_RECYCLE", 300))
    """Amount of time to wait before recycling connections."""
    POOL_PRE_PING: bool = field(default_factory=get_env("DATABASE_PRE_POOL_PING", False))
    """Optionally ping database before fetching a session from the connection pool."""
    URL: str = field(default_factory=get_env("DATABASE_URL", "sqlite+aiosqlite:///db.sqlite3"))
    """SQLAlchemy Database URL."""
    MIGRATION_CONFIG: str = f"{BASE_DIR}/db/migrations/alembic.ini"
    """The path to the `alembic.ini` configuration file."""
    MIGRATION_PATH: str = f"{BASE_DIR}/db/migrations"
    """The path to the `alembic` database migrations."""
    MIGRATION_DDL_VERSION_TABLE: str = "ddl_version"
    """The name to use for the `alembic` versions table name."""
    FIXTURE_PATH: str = f"{BASE_DIR}/db/fixtures"
    """The path to JSON fixture files to load into tables."""
    _engine_instance: AsyncEngine | None = None
    """SQLAlchemy engine instance generated from settings."""

    @property
    def engine(self) -> AsyncEngine:
        return self.get_engine()

    def get_engine(self) -> AsyncEngine:
        if self._engine_instance is not None:
            return self._engine_instance
        from app.utils.engine_factory import create_sqlalchemy_engine

        self._engine_instance = create_sqlalchemy_engine(self)
        return self._engine_instance


@dataclass
class ViteSettings:
    """Vite development server configuration.

    Note: host/port are auto-managed by litestar-vite plugin.
    """

    DEV_MODE: bool = field(default_factory=get_env("VITE_DEV_MODE", False))
    """Start `vite` development server."""
    TEMPLATE_DIR: Path = field(default_factory=get_env("VITE_TEMPLATE_DIR", Path(f"{BASE_DIR.parent}/resources")))
    """Template directory."""


@dataclass
class ServerSettings:
    """Server configurations."""

    APP_LOC: str = "app.server.asgi:create_app"
    """Path to app executable, or factory."""
    HOST: str = field(default_factory=get_env("LITESTAR_HOST", "0.0.0.0"))  # noqa: S104
    """Server network host."""
    PORT: int = field(default_factory=get_env("LITESTAR_PORT", 8000))
    """Server port."""
    KEEPALIVE: int = field(default_factory=get_env("LITESTAR_KEEPALIVE", 65))
    """Seconds to hold connections open (65 is > AWS lb idle timeout)."""
    RELOAD: bool = field(default_factory=get_env("LITESTAR_RELOAD", False))
    """Turn on hot reloading."""
    RELOAD_DIRS: list[str] = field(default_factory=get_env("LITESTAR_RELOAD_DIRS", [f"{BASE_DIR}"]))
    """Directories to watch for reloading."""
    HTTP_WORKERS: int | None = field(
        default_factory=lambda: int(os.getenv("WEB_CONCURRENCY")) if os.getenv("WEB_CONCURRENCY") is not None else None,  # type: ignore[arg-type]
    )
    """Number of HTTP Worker processes to be spawned by Uvicorn."""


@dataclass
class LogSettings:
    """Logger configuration"""

    # https://stackoverflow.com/a/1845097/6560549
    EXCLUDE_PATHS: str = r"\A(?!x)x"
    """Regex to exclude paths from logging."""
    HTTP_EVENT: str = "HTTP"
    """Log event name for logs from Litestar handlers."""
    INCLUDE_COMPRESSED_BODY: bool = False
    """Include 'body' of compressed responses in log output."""
    LEVEL: int = field(default_factory=get_env("LOG_LEVEL", 10))
    """Stdlib log levels. Only emit logs at this level, or higher."""
    OBFUSCATE_COOKIES: set[str] = field(default_factory=lambda: {"session", "XSRF-TOKEN"})
    """Request cookie keys to obfuscate."""
    OBFUSCATE_HEADERS: set[str] = field(default_factory=lambda: {"Authorization", "X-API-KEY", "X-XSRF-TOKEN"})
    """Request header keys to obfuscate."""
    REQUEST_FIELDS: list[RequestExtractorField] = field(
        default_factory=lambda: [
            "path",
            "method",
            "query",
            "path_params",
        ],
    )
    """Attributes of the [Request][litestar.connection.request.Request] to be logged."""
    RESPONSE_FIELDS: list[ResponseExtractorField] = field(
        default_factory=lambda: [
            "status_code",
        ],
    )
    """Attributes of the [Response][litestar.response.Response] to be logged."""
    SQLALCHEMY_LEVEL: int = field(default_factory=get_env("SQLALCHEMY_LOG_LEVEL", 20))
    """Level to log SQLAlchemy logs."""
    UVICORN_ACCESS_LEVEL: int = 20
    """Level to log uvicorn access logs."""
    UVICORN_ERROR_LEVEL: int = 20
    """Level to log uvicorn error logs."""
    GRANIAN_ACCESS_LEVEL: int = field(default_factory=get_env("GRANIAN_ACCESS_LOG_LEVEL", 30))
    """Level to log granian access logs."""
    GRANIAN_ERROR_LEVEL: int = field(default_factory=get_env("GRANIAN_ERROR_LOG_LEVEL", 20))
    """Level to log granian error logs."""


@dataclass
class AppSettings:
    """Application configuration"""

    URL: str = field(default_factory=get_env("APP_URL", "http://localhost:8000"))
    """The frontend base URL"""
    DEBUG: bool = field(default_factory=get_env("LITESTAR_DEBUG", False))
    """Run `Litestar` with `debug=True`."""
    SECRET_KEY: str = field(
        default_factory=lambda: os.getenv("SECRET_KEY", binascii.hexlify(os.urandom(32)).decode(encoding="utf-8")),
    )
    """Application secret key."""
    NAME: str = field(default_factory=get_env("APP_NAME", "app"))
    """Application name."""
    ALLOWED_CORS_ORIGINS: list[str] = field(default_factory=get_env("ALLOWED_CORS_ORIGINS", ["*"]))
    """Allowed CORS Origins"""
    CSRF_COOKIE_NAME: str = field(default_factory=get_env("CSRF_COOKIE_NAME", "XSRF-TOKEN"))
    """CSRF Cookie Name"""
    CSRF_HEADER_NAME: str = field(default_factory=get_env("CSRF_HEADER_NAME", "X-XSRF-TOKEN"))
    """CSRF Header Name"""
    CSRF_COOKIE_SECURE: bool = field(default_factory=get_env("CSRF_COOKIE_SECURE", False))
    """CSRF Secure Cookie"""
    GITHUB_OAUTH2_CLIENT_ID: str = field(default_factory=get_env("GITHUB_OAUTH2_CLIENT_ID", ""))
    """GitHub Client ID"""
    GITHUB_OAUTH2_CLIENT_SECRET: str = field(default_factory=get_env("GITHUB_OAUTH2_CLIENT_SECRET", ""))
    """GitHub Client Secret"""
    GOOGLE_OAUTH2_CLIENT_ID: str = field(default_factory=get_env("GOOGLE_OAUTH2_CLIENT_ID", ""))
    """Google Client ID"""
    GOOGLE_OAUTH2_CLIENT_SECRET: str = field(default_factory=get_env("GOOGLE_OAUTH2_CLIENT_SECRET", ""))
    """Google Client Secret"""

    @property
    def slug(self) -> str:
        """Return a slugified name.

        Returns:
            `self.NAME`, all lowercase and hyphens instead of spaces.
        """
        return slugify(self.NAME)


@dataclass
class Settings:
    app: AppSettings = field(default_factory=AppSettings)
    db: DatabaseSettings = field(default_factory=DatabaseSettings)
    vite: ViteSettings = field(default_factory=ViteSettings)
    server: ServerSettings = field(default_factory=ServerSettings)
    log: LogSettings = field(default_factory=LogSettings)

    @classmethod
    @lru_cache(maxsize=1, typed=True)
    def from_env(cls, dotenv_filename: str = ".env") -> Settings:
        from litestar.cli._utils import console

        env_file = Path(f"{os.curdir}/{dotenv_filename}")
        if env_file.is_file():
            from dotenv import load_dotenv

            console.print(f"[yellow]Loading environment configuration from {dotenv_filename}[/]")

            load_dotenv(env_file, override=True)
        return Settings()


def get_settings(dotenv_filename: str = ".env") -> Settings:
    return Settings.from_env(dotenv_filename)

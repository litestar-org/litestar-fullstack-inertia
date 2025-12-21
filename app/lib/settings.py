from __future__ import annotations

import binascii
import os
import sys
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

from advanced_alchemy.utils.text import slugify
from litestar.utils.module_loader import module_to_os_path
from sqlalchemy.ext.asyncio import AsyncEngine

from app.utils.engine_factory import create_sqlalchemy_engine
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

    EXCLUDE_PATHS: str = r"^/static/"
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
        default_factory=lambda: ["path", "method", "query", "path_params"],
    )
    """Attributes of the [Request][litestar.connection.request.Request] to be logged."""
    RESPONSE_FIELDS: list[ResponseExtractorField] = field(default_factory=lambda: ["status_code"])
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

    def create_structlog_config(self) -> Any:
        """Create the complete Litestar StructlogConfig.

        Returns:
            Configured StructlogConfig for Litestar application.
        """
        import logging

        import structlog
        from litestar.exceptions import NotAuthorizedException, NotFoundException, PermissionDeniedException
        from litestar.logging.config import LoggingConfig, StructLoggingConfig, default_logger_factory
        from litestar.middleware.logging import LoggingMiddlewareConfig
        from litestar.plugins.structlog import StructlogConfig

        from app.lib import log as log_conf

        as_json = not log_conf.is_tty()
        disable_stack_trace: set[Any] = {
            404,
            401,
            403,
            NotFoundException,
            NotAuthorizedException,
            PermissionDeniedException,
        }

        return StructlogConfig(
            enable_middleware_logging=False,
            structlog_logging_config=StructLoggingConfig(
                log_exceptions="always",
                processors=log_conf.structlog_processors(as_json=as_json),
                logger_factory=default_logger_factory(as_json=as_json),
                disable_stack_trace=disable_stack_trace,
                standard_lib_logging_config=LoggingConfig(
                    log_exceptions="always",
                    disable_existing_loggers=True,
                    disable_stack_trace=disable_stack_trace,
                    root={"level": logging.getLevelName(self.LEVEL), "handlers": ["queue_listener"]},
                    formatters={
                        "standard": {
                            "()": structlog.stdlib.ProcessorFormatter,
                            "processors": log_conf.stdlib_logger_processors(as_json=as_json),
                        },
                    },
                    loggers={
                        "sqlalchemy.engine": {
                            "propagate": False,
                            "level": self.SQLALCHEMY_LEVEL,
                            "handlers": ["queue_listener"],
                        },
                        "sqlalchemy.engine.Engine": {
                            "propagate": False,
                            "level": self.SQLALCHEMY_LEVEL,
                            "handlers": ["queue_listener"],
                        },
                        "sqlalchemy.pool": {
                            "propagate": False,
                            "level": self.SQLALCHEMY_LEVEL,
                            "handlers": ["queue_listener"],
                        },
                        "urllib3": {"propagate": False, "level": self.SQLALCHEMY_LEVEL, "handlers": ["queue_listener"]},
                        "_granian": {
                            "propagate": False,
                            "level": self.GRANIAN_ERROR_LEVEL,
                            "handlers": ["queue_listener"],
                        },
                        "granian.server": {
                            "propagate": False,
                            "level": self.GRANIAN_ERROR_LEVEL,
                            "handlers": ["queue_listener"],
                        },
                        "granian.access": {
                            "propagate": False,
                            "level": self.GRANIAN_ACCESS_LEVEL,
                            "handlers": ["queue_listener"],
                        },
                        "uvicorn.error": {
                            "propagate": False,
                            "level": self.UVICORN_ERROR_LEVEL,
                            "handlers": ["queue_listener"],
                        },
                        "uvicorn.access": {
                            "propagate": False,
                            "level": self.UVICORN_ACCESS_LEVEL,
                            "handlers": ["queue_listener"],
                        },
                        "httpx": {"propagate": False, "level": logging.WARNING, "handlers": ["queue_listener"]},
                        "httpcore": {"propagate": False, "level": logging.WARNING, "handlers": ["queue_listener"]},
                    },
                ),
            ),
            middleware_logging_config=LoggingMiddlewareConfig(
                request_log_fields=self.REQUEST_FIELDS, response_log_fields=self.RESPONSE_FIELDS,
            ),
        )


@dataclass
class EmailSettings:
    """Email service configuration."""

    ENABLED: bool = field(default_factory=get_env("EMAIL_ENABLED", False))
    """Enable email sending. If False, emails are logged but not sent."""
    BACKEND: str = field(default_factory=get_env("EMAIL_BACKEND", "console"))
    """Email backend: 'smtp', 'console', or 'locmem'."""
    FROM_EMAIL: str = field(default_factory=get_env("EMAIL_FROM", "noreply@example.com"))
    """Default from email address."""

    # SMTP Settings
    SMTP_HOST: str = field(default_factory=get_env("EMAIL_SMTP_HOST", "localhost"))
    """SMTP server hostname."""
    SMTP_PORT: int = field(default_factory=get_env("EMAIL_SMTP_PORT", 587))
    """SMTP server port."""
    SMTP_USER: str = field(default_factory=get_env("EMAIL_SMTP_USER", ""))
    """SMTP username for authentication."""
    SMTP_PASSWORD: str = field(default_factory=get_env("EMAIL_SMTP_PASSWORD", ""))
    """SMTP password for authentication."""
    SMTP_USE_TLS: bool = field(default_factory=get_env("EMAIL_SMTP_USE_TLS", True))
    """Use STARTTLS for SMTP connection."""
    SMTP_USE_SSL: bool = field(default_factory=get_env("EMAIL_SMTP_USE_SSL", False))
    """Use implicit SSL for SMTP connection."""
    SMTP_TIMEOUT: int = field(default_factory=get_env("EMAIL_SMTP_TIMEOUT", 30))
    """SMTP connection timeout in seconds."""

    # Token expiration settings
    VERIFICATION_TOKEN_EXPIRES_HOURS: int = field(default_factory=get_env("EMAIL_VERIFICATION_TOKEN_EXPIRES_HOURS", 24))
    """Hours until email verification token expires."""
    PASSWORD_RESET_TOKEN_EXPIRES_MINUTES: int = field(
        default_factory=get_env("EMAIL_PASSWORD_RESET_TOKEN_EXPIRES_MINUTES", 60),
    )
    """Minutes until password reset token expires."""
    INVITATION_TOKEN_EXPIRES_DAYS: int = field(default_factory=get_env("EMAIL_INVITATION_TOKEN_EXPIRES_DAYS", 7))
    """Days until team invitation token expires."""


@dataclass
class StorageSettings:
    """File storage configuration."""

    BACKEND: str = field(default_factory=get_env("STORAGE_BACKEND", "local"))
    """Storage backend: 'local', 's3', 'gcs', or 'azure'."""
    UPLOAD_DIR: Path = field(default_factory=get_env("STORAGE_UPLOAD_DIR", Path("uploads")))
    """Directory for file uploads (local backend only)."""
    BUCKET: str = field(default_factory=get_env("STORAGE_BUCKET", ""))
    """Cloud storage bucket name (s3/gcs/azure)."""
    SIGNED_URL_EXPIRY: int = field(default_factory=get_env("STORAGE_SIGNED_URL_EXPIRY", 3600))
    """Signed URL expiry time in seconds."""

    # AWS S3 settings
    AWS_ACCESS_KEY_ID: str = field(default_factory=get_env("AWS_ACCESS_KEY_ID", ""))
    """AWS access key ID."""
    AWS_SECRET_ACCESS_KEY: str = field(default_factory=get_env("AWS_SECRET_ACCESS_KEY", ""))
    """AWS secret access key."""
    AWS_REGION: str = field(default_factory=get_env("AWS_REGION", "us-east-1"))
    """AWS region."""
    AWS_ENDPOINT: str = field(default_factory=get_env("AWS_ENDPOINT", ""))
    """Custom S3 endpoint (for MinIO, etc.)."""

    # GCS settings
    GOOGLE_SERVICE_ACCOUNT: str = field(default_factory=get_env("GOOGLE_SERVICE_ACCOUNT", ""))
    """Path to GCS service account JSON file."""

    # Azure settings
    AZURE_CONNECTION_STRING: str = field(default_factory=get_env("AZURE_STORAGE_CONNECTION_STRING", ""))
    """Azure storage connection string."""

    MAX_AVATAR_SIZE: int = field(default_factory=get_env("MAX_AVATAR_SIZE", 5 * 1024 * 1024))
    """Maximum avatar file size in bytes (5MB)."""
    ALLOWED_AVATAR_TYPES: tuple[str, ...] = ("image/jpeg", "image/png", "image/gif", "image/webp")
    """Allowed MIME types for avatars."""

    @property
    def is_cloud_storage(self) -> bool:
        """Check if using cloud storage backend."""
        return self.BACKEND in {"s3", "gcs", "azure"}


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
    REGISTRATION_ENABLED: bool = field(default_factory=get_env("REGISTRATION_ENABLED", True))
    """Enable user registration. If False, only existing users can log in."""
    MFA_ENABLED: bool = field(default_factory=get_env("MFA_ENABLED", False))
    """Enable Multi-Factor Authentication (TOTP) support in the UI."""

    @property
    def slug(self) -> str:
        """Return a slugified name.

        Returns:
            `self.NAME`, all lowercase and hyphens instead of spaces.
        """
        return slugify(self.NAME)

    @property
    def github_oauth_enabled(self) -> bool:
        """Check if GitHub OAuth is configured.

        Returns:
            True if both client ID and secret are set.
        """
        return bool(self.GITHUB_OAUTH2_CLIENT_ID and self.GITHUB_OAUTH2_CLIENT_SECRET)

    @property
    def google_oauth_enabled(self) -> bool:
        """Check if Google OAuth is configured.

        Returns:
            True if both client ID and secret are set.
        """
        return bool(self.GOOGLE_OAUTH2_CLIENT_ID and self.GOOGLE_OAUTH2_CLIENT_SECRET)


@dataclass
class Settings:
    app: AppSettings = field(default_factory=AppSettings)
    db: DatabaseSettings = field(default_factory=DatabaseSettings)
    email: EmailSettings = field(default_factory=EmailSettings)
    storage: StorageSettings = field(default_factory=StorageSettings)
    vite: ViteSettings = field(default_factory=ViteSettings)
    server: ServerSettings = field(default_factory=ServerSettings)
    log: LogSettings = field(default_factory=LogSettings)

    @classmethod
    @lru_cache(maxsize=1, typed=True)
    def from_env(cls, dotenv_filename: str = ".env") -> Settings:
        import structlog
        from dotenv import load_dotenv
        from litestar.cli._utils import console

        logger = structlog.get_logger()
        env_file = Path(f"{os.curdir}/{dotenv_filename}")
        env_file_exists = env_file.is_file()
        original_env = os.environ.copy()
        if env_file_exists:
            console.print(f"[yellow]Loading environment configuration from {dotenv_filename}[/]")
            load_dotenv(env_file, override=False)
        try:
            settings = Settings()
        except Exception as e:  # noqa: BLE001
            logger.fatal("Could not load settings. %s", e)
            sys.exit(1)
        finally:
            os.environ.clear()
            os.environ.update(original_env)
        return settings


def get_settings(dotenv_filename: str = ".env") -> Settings:
    return Settings.from_env(dotenv_filename)

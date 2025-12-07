import logging
import sys
from functools import lru_cache
from pathlib import Path
from typing import cast

import logfire
import structlog
from httpx_oauth.clients.github import GitHubOAuth2
from httpx_oauth.clients.google import GoogleOAuth2
from litestar.config.compression import CompressionConfig
from litestar.config.cors import CORSConfig
from litestar.config.csrf import CSRFConfig
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.logging.config import (
    LoggingConfig,
    StructLoggingConfig,
    default_logger_factory,
    default_structlog_processors,
    default_structlog_standard_lib_processors,
)
from litestar.middleware.logging import LoggingMiddlewareConfig
from litestar.middleware.session.server_side import ServerSideSessionConfig
from litestar.plugins.sqlalchemy import (
    AlembicAsyncConfig,
    AsyncSessionConfig,
    SQLAlchemyAsyncConfig,
)
from litestar.plugins.structlog import StructlogConfig
from litestar.template import TemplateConfig
from litestar_vite import InertiaConfig, PathConfig, TypeGenConfig, ViteConfig

from app.lib.settings import BASE_DIR, get_settings

settings = get_settings()


compression = CompressionConfig(backend="gzip")
csrf = CSRFConfig(
    secret=settings.app.SECRET_KEY,
    cookie_secure=settings.app.CSRF_COOKIE_SECURE,
    cookie_name=settings.app.CSRF_COOKIE_NAME,
    header_name=settings.app.CSRF_HEADER_NAME,
)
cors = CORSConfig(allow_origins=cast("list[str]", settings.app.ALLOWED_CORS_ORIGINS))


alchemy = SQLAlchemyAsyncConfig(
    engine_instance=settings.db.get_engine(),
    before_send_handler="autocommit_include_redirects",
    session_config=AsyncSessionConfig(expire_on_commit=False),
    alembic_config=AlembicAsyncConfig(
        version_table_name=settings.db.MIGRATION_DDL_VERSION_TABLE,
        script_config=settings.db.MIGRATION_CONFIG,
        script_location=settings.db.MIGRATION_PATH,
    ),
)
templates = TemplateConfig(engine=JinjaTemplateEngine(directory=settings.vite.TEMPLATE_DIR))
vite = ViteConfig(
    dev_mode=settings.vite.DEV_MODE,
    paths=PathConfig(
        root=BASE_DIR.parent,
        bundle_dir=Path("app/domain/web/public"),
        resource_dir=Path("resources"),
    ),
    inertia=InertiaConfig(
        root_template="index.html",
        redirect_unauthorized_to="/login",
        extra_static_page_props={
            "canResetPassword": True,
            "hasTermsAndPrivacyPolicyFeature": True,
            "mustVerifyEmail": True,
        },
        extra_session_page_props={"currentTeam"},
    ),
    types=TypeGenConfig(
        output=BASE_DIR.parent / "resources" / "lib" / "generated",
    ),
)
session = ServerSideSessionConfig(max_age=3600)


@lru_cache
def _is_tty() -> bool:
    return bool(sys.stderr.isatty() or sys.stdout.isatty())


_render_as_json = not _is_tty()
_structlog_default_processors = default_structlog_processors(as_json=_render_as_json)
_structlog_default_processors.insert(1, structlog.processors.EventRenamer("message"))
_structlog_standard_lib_processors = default_structlog_standard_lib_processors(as_json=_render_as_json)
_structlog_standard_lib_processors.insert(1, structlog.processors.EventRenamer("message"))

if settings.app.OPENTELEMETRY_ENABLED:
    _structlog_default_processors.insert(-1, logfire.StructlogProcessor())
log = StructlogConfig(
    enable_middleware_logging=False,
    structlog_logging_config=StructLoggingConfig(
        log_exceptions="always",
        processors=_structlog_default_processors,
        logger_factory=default_logger_factory(as_json=_render_as_json),
        standard_lib_logging_config=LoggingConfig(
            root={"level": logging.getLevelName(settings.log.LEVEL), "handlers": ["queue_listener"]},
            formatters={
                "standard": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processors": _structlog_standard_lib_processors,
                },
            },
            loggers={
                "sqlalchemy.engine": {
                    "propagate": False,
                    "level": settings.log.SQLALCHEMY_LEVEL,
                    "handlers": ["queue_listener"],
                },
                "sqlalchemy.pool": {
                    "propagate": False,
                    "level": settings.log.SQLALCHEMY_LEVEL,
                    "handlers": ["queue_listener"],
                },
                "logfire": {
                    "propagate": False,
                    "level": settings.log.SQLALCHEMY_LEVEL,
                    "handlers": ["queue_listener"],
                },
                "urllib3": {
                    "propagate": False,
                    "level": settings.log.SQLALCHEMY_LEVEL,
                    "handlers": ["queue_listener"],
                },
                "_granian": {
                    "propagate": False,
                    "level": settings.log.GRANIAN_ERROR_LEVEL,
                    "handlers": ["queue_listener"],
                },
                "granian.server": {
                    "propagate": False,
                    "level": settings.log.GRANIAN_ERROR_LEVEL,
                    "handlers": ["queue_listener"],
                },
                "granian.access": {
                    "propagate": False,
                    "level": settings.log.GRANIAN_ACCESS_LEVEL,
                    "handlers": ["queue_listener"],
                },
                "opentelemetry.sdk.metrics._internal": {
                    "propagate": False,
                    "level": 40,
                    "handlers": ["queue_listener"],
                },
            },
        ),
    ),
    middleware_logging_config=LoggingMiddlewareConfig(
        request_log_fields=["method", "path", "path_params", "query"],
        response_log_fields=["status_code"],
    ),
)

github_oauth2_client = GitHubOAuth2(
    client_id=settings.app.GITHUB_OAUTH2_CLIENT_ID,
    client_secret=settings.app.GITHUB_OAUTH2_CLIENT_SECRET,
)
google_oauth2_client = GoogleOAuth2(
    client_id=settings.app.GOOGLE_OAUTH2_CLIENT_ID,
    client_secret=settings.app.GOOGLE_OAUTH2_CLIENT_SECRET,
)

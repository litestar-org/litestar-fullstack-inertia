# pylint: disable=[invalid-name,import-outside-toplevel]
from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar
from uuid import UUID

from litestar.config.response_cache import ResponseCacheConfig, default_cache_key_builder
from litestar.di import Provide
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin, SwaggerRenderPlugin
from litestar.plugins import CLIPluginProtocol, InitPluginProtocol
from litestar.stores.redis import RedisStore
from litestar.stores.registry import StoreRegistry

if TYPE_CHECKING:
    from click import Group
    from litestar import Request
    from litestar.config.app import AppConfig
    from redis.asyncio import Redis


T = TypeVar("T")


class ApplicationCore(InitPluginProtocol, CLIPluginProtocol):
    """Application core configuration plugin.

    This class is responsible for configuring the main Litestar application with our routes, guards, and various plugins

    """

    __slots__ = ("app_slug", "redis")
    redis: Redis
    app_slug: str

    def __init__(self) -> None:
        """Initialize ``ApplicationConfigurator``.

        Args:
            config: configure and start SAQ.
        """

    def on_cli_init(self, cli: Group) -> None:
        from app.cli import user_management_app
        from app.lib.settings import get_settings

        settings = get_settings()
        self.redis = settings.redis.get_client()
        self.app_slug = settings.app.slug
        cli.add_command(user_management_app)

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        """Configure application for use with SQLAlchemy.

        Args:
            app_config: The :class:`AppConfig <.config.app.AppConfig>` instance.
        """


        from app import config
        from app.__metadata__ import __version__ as current_version
        from app.db.models import User as UserModel
        from app.domain.accounts import signals as account_signals
        from app.domain.accounts.controllers import (
            AccessController,
            ProfileController,
            RegistrationController,
            UserController,
            UserRoleController,
        )
        from app.domain.accounts.dependencies import provide_user
        from app.domain.accounts.guards import session_auth
        from app.domain.tags.controllers import TagController
        from app.domain.teams import signals as team_signals
        from app.domain.teams.controllers import TeamController, TeamMemberController
        from app.domain.web.controllers import WebController
        from app.lib import log
        from app.lib.dependencies import create_collection_dependencies
        from app.lib.settings import get_settings
        from app.server import plugins

        settings = get_settings()
        self.redis = settings.redis.get_client()
        self.app_slug = settings.app.slug
        # monitoring
        if settings.app.OPENTELEMETRY_ENABLED:
            import logfire

            from app.lib.otel import configure_instrumentation

            logfire.configure()
            otel_config = configure_instrumentation()
            app_config.middleware.insert(0, otel_config.middleware)
        app_config.debug = settings.app.DEBUG
        # openapi
        app_config.openapi_config = OpenAPIConfig(
            title=settings.app.NAME,
            version=current_version,
            use_handler_docstrings=True,
            render_plugins=[ScalarRenderPlugin(version="latest"), SwaggerRenderPlugin()],
        )
        # session auth (updates openapi config)
        app_config = session_auth.on_app_init(app_config)
        # log
        app_config.middleware.insert(0, log.StructlogMiddleware)
        app_config.after_exception.append(log.after_exception_hook_handler)
        app_config.before_send.append(log.BeforeSendHandler())
        # security
        app_config.cors_config = config.cors
        app_config.csrf_config = config.csrf
        # plugins
        app_config.plugins.extend(
            [
                plugins.structlog,
                plugins.flasher,
                plugins.granian,
                plugins.alchemy,
                plugins.vite,
                plugins.saq,
                plugins.inertia,
            ],
        )

        # routes
        app_config.route_handlers.extend(
            [
                AccessController,
                ProfileController,
                RegistrationController,
                UserController,
                TeamController,
                UserRoleController,
                #  TeamInvitationController,
                TeamMemberController,
                TagController,
                WebController,
            ],
        )
        # signatures
        app_config.signature_namespace.update({"UserModel": UserModel, "UUID":UUID})
        # caching & redis
        app_config.response_cache_config = ResponseCacheConfig(
            default_expiration=120,
            key_builder=self._cache_key_builder,
        )
        app_config.stores = StoreRegistry(default_factory=self.redis_store_factory)
        app_config.on_shutdown.append(self.redis.aclose)  # type: ignore[attr-defined]
        # dependencies
        dependencies = {"current_user": Provide(provide_user)}
        dependencies.update(create_collection_dependencies())
        app_config.dependencies.update(dependencies)
        # listeners
        app_config.listeners.extend(
            [account_signals.user_created_event_handler, team_signals.team_created_event_handler],
        )
        return app_config

    def redis_store_factory(self, name: str) -> RedisStore:
        return RedisStore(self.redis, namespace=f"{self.app_slug}:{name}")

    def _cache_key_builder(self, request: Request) -> str:
        """App name prefixed cache key builder.

        Args:
            request (Request): Current request instance.

        Returns:
            str: App slug prefixed cache key.
        """

        return f"{self.app_slug}:{default_cache_key_builder(request)}"

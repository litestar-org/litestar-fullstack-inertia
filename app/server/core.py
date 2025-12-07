# pylint: disable=[invalid-name,import-outside-toplevel]
from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.exceptions.responses import create_debug_response, create_exception_response
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin, SwaggerRenderPlugin
from litestar.plugins import CLIPluginProtocol, InitPluginProtocol

if TYPE_CHECKING:
    from click import Group
    from litestar.config.app import AppConfig
    from litestar.connection import Request
    from litestar.response import Response


T = TypeVar("T")


def _http_exception_handler(request: "Request[Any, Any, Any]", exc: HTTPException) -> "Response[Any]":
    """Handle HTTPException properly.

    Workaround for litestar-vite issue #122 where the Inertia exception handler
    converts HTTPException to 500 for non-Inertia requests.

    For API routes (/api/*), return proper HTTP status codes.
    For Inertia page routes, delegate to Inertia exception handler for redirects.
    """
    # API routes should return proper HTTP status codes
    is_api_route = request.url.path.startswith("/api/")

    if is_api_route:
        # Return proper HTTP response for API routes
        if request.app.debug:
            return cast("Response[Any]", create_debug_response(request, exc))
        return cast("Response[Any]", create_exception_response(request, exc))

    # For non-API routes (Inertia pages), use Inertia exception handling
    # This handles redirects for 401/403 errors on page routes
    from litestar_vite.inertia.exception_handler import create_inertia_exception_response

    return create_inertia_exception_response(request, exc)


class ApplicationCore(InitPluginProtocol, CLIPluginProtocol):
    """Application core configuration plugin.

    This class is responsible for configuring the main Litestar application with our routes, guards, and various plugins

    """

    __slots__ = ("app_slug",)
    app_slug: str

    def __init__(self) -> None:
        """Initialize ``ApplicationConfigurator``."""

    def on_cli_init(self, cli: Group) -> None:
        from app.cli import user_management_app
        from app.lib.settings import get_settings

        settings = get_settings()
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
        # templates
        app_config.template_config = config.templates
        # exception handlers - workaround for litestar-vite #122
        if app_config.exception_handlers is None:
            app_config.exception_handlers = {}
        app_config.exception_handlers[HTTPException] = _http_exception_handler
        # plugins
        app_config.plugins.extend(
            [
                plugins.structlog,
                plugins.flasher,
                plugins.granian,
                plugins.alchemy,
                plugins.vite,
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
        app_config.signature_namespace.update({"UserModel": UserModel, "UUID": UUID})
        # dependencies
        dependencies = {"current_user": Provide(provide_user)}
        dependencies.update(create_collection_dependencies())
        app_config.dependencies.update(dependencies)
        # listeners
        app_config.listeners.extend(
            [account_signals.user_created_event_handler, team_signals.team_created_event_handler],
        )
        return app_config

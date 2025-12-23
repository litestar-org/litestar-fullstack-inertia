# pylint: disable=[invalid-name,import-outside-toplevel]
from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from litestar import get
from litestar.di import Provide
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin, SwaggerRenderPlugin
from litestar.plugins import CLIPluginProtocol, InitPluginProtocol
from litestar.static_files import create_static_files_router


@get("/health", exclude_from_auth=True, include_in_schema=False)
async def health_check() -> dict[str, str]:
    """Health check endpoint for Railway and load balancers."""
    return {"status": "ok"}


if TYPE_CHECKING:
    from click import Group
    from litestar.config.app import AppConfig


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

        Returns:
            The modified :class:`AppConfig <.config.app.AppConfig>` instance.
        """

        from advanced_alchemy.exceptions import IntegrityError, NotFoundError, RepositoryError

        from app import config
        from app.__metadata__ import __version__ as current_version
        from app.db.models import User as UserModel
        from app.domain.accounts import signals as account_signals
        from app.domain.accounts.controllers import (
            AccessController,
            EmailVerificationController,
            MfaChallengeController,
            MfaController,
            OAuthAccountController,
            PasswordResetController,
            ProfileController,
            RegistrationController,
            UserController,
            UserRoleController,
        )
        from app.domain.accounts.dependencies import provide_user
        from app.domain.accounts.guards import session_auth
        from app.domain.accounts.services import (
            EmailTokenService,
            RoleService,
            UserOAuthAccountService,
            UserRoleService,
            UserService,
        )
        from app.domain.admin.controllers import (
            AdminAuditController,
            AdminDashboardController,
            AdminTeamController,
            AdminUserController,
        )
        from app.domain.admin.services import AuditLogService
        from app.domain.tags.controllers import TagController
        from app.domain.tags.services import TagService
        from app.domain.teams import signals as team_signals
        from app.domain.teams.controllers import (
            InvitationAcceptController,
            TeamController,
            TeamInvitationController,
            TeamMemberController,
            UserInvitationsController,
        )
        from app.domain.teams.services import TeamInvitationService, TeamMemberService, TeamService
        from app.domain.web.controllers import WebController
        from app.lib import log
        from app.lib.exceptions import (
            inertia_exception_handler,
            integrity_error_handler,
            not_found_error_handler,
            repository_error_handler,
        )
        from app.lib.settings import Settings, get_settings
        from app.server import plugins

        settings = get_settings()
        self.app_slug = settings.app.slug
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
        # Exception handlers for database errors (order matters - more specific first)
        app_config.exception_handlers.update({
            IntegrityError: integrity_error_handler,
            NotFoundError: not_found_error_handler,
            RepositoryError: repository_error_handler,
            Exception: inertia_exception_handler,
        })
        # security
        app_config.cors_config = config.cors
        app_config.csrf_config = config.csrf
        # templates
        app_config.template_config = config.templates
        # plugins
        app_config.plugins.extend([plugins.structlog, plugins.granian, plugins.alchemy, plugins.vite])

        # static files for uploads
        uploads_router = create_static_files_router(
            directories=[settings.storage.UPLOAD_DIR],
            path="/uploads",
            name="uploads",
        )

        # routes
        app_config.route_handlers.extend([
            health_check,
            uploads_router,
            AccessController,
            EmailVerificationController,
            MfaChallengeController,
            MfaController,
            OAuthAccountController,
            PasswordResetController,
            ProfileController,
            RegistrationController,
            UserController,
            TeamController,
            UserRoleController,
            TeamInvitationController,
            TeamMemberController,
            InvitationAcceptController,
            UserInvitationsController,
            TagController,
            WebController,
            # Admin controllers
            AdminDashboardController,
            AdminUserController,
            AdminTeamController,
            AdminAuditController,
        ])
        # signatures
        app_config.signature_namespace.update({
            "UUID": UUID,
            "UserModel": UserModel,
            "AuditLogService": AuditLogService,
            "EmailTokenService": EmailTokenService,
            "RoleService": RoleService,
            "TagService": TagService,
            "TeamInvitationService": TeamInvitationService,
            "TeamMemberService": TeamMemberService,
            "TeamService": TeamService,
            "UserOAuthAccountService": UserOAuthAccountService,
            "UserRoleService": UserRoleService,
            "UserService": UserService,
            "Settings": Settings,
        })
        # dependencies
        app_config.dependencies.update({
            "current_user": Provide(provide_user),
            "settings": Provide(get_settings, sync_to_thread=False),
        })
        # listeners
        app_config.listeners.extend([
            account_signals.user_created_event_handler,
            account_signals.user_verified_event_handler,
            account_signals.password_reset_requested_handler,
            account_signals.password_reset_completed_handler,
            team_signals.team_created_event_handler,
            team_signals.team_invitation_created_handler,
        ])
        return app_config

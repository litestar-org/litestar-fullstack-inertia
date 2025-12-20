from pathlib import Path

from advanced_alchemy.extensions.litestar import AlembicAsyncConfig, AsyncSessionConfig, SQLAlchemyAsyncConfig
from httpx_oauth.clients.github import GitHubOAuth2
from httpx_oauth.clients.google import GoogleOAuth2
from litestar.config.compression import CompressionConfig
from litestar.config.cors import CORSConfig
from litestar.config.csrf import CSRFConfig
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.middleware.session.server_side import ServerSideSessionConfig
from litestar.template import TemplateConfig
from litestar_vite import InertiaConfig, PathConfig, RuntimeConfig, TypeGenConfig, ViteConfig

from app.domain.teams.schemas import CurrentTeam
from app.lib.settings import BASE_DIR, get_settings

settings = get_settings()


compression = CompressionConfig(backend="gzip")
csrf = CSRFConfig(
    secret=settings.app.SECRET_KEY,
    cookie_secure=settings.app.CSRF_COOKIE_SECURE,
    cookie_name=settings.app.CSRF_COOKIE_NAME,
    header_name=settings.app.CSRF_HEADER_NAME,
)
cors = CORSConfig(allow_origins=settings.app.ALLOWED_CORS_ORIGINS)


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
    runtime=RuntimeConfig(executor="bun"),
    paths=PathConfig(root=BASE_DIR.parent, bundle_dir=Path("app/domain/web/public"), resource_dir=Path("resources")),
    inertia=InertiaConfig(
        redirect_unauthorized_to="/login",
        extra_static_page_props={
            "canResetPassword": True,
            "hasTermsAndPrivacyPolicyFeature": True,
            "mustVerifyEmail": True,
            "githubOAuthEnabled": settings.app.github_oauth_enabled,
            "googleOAuthEnabled": settings.app.google_oauth_enabled,
            "registrationEnabled": settings.app.REGISTRATION_ENABLED,
            "mfaEnabled": settings.app.MFA_ENABLED,
        },
        extra_session_page_props={"currentTeam": CurrentTeam},
    ),
    types=TypeGenConfig(output=BASE_DIR.parent / "resources" / "lib" / "generated"),
)
session = ServerSideSessionConfig(max_age=3600)

log = settings.log.create_structlog_config()

github_oauth2_client = GitHubOAuth2(
    client_id=settings.app.GITHUB_OAUTH2_CLIENT_ID, client_secret=settings.app.GITHUB_OAUTH2_CLIENT_SECRET,
)
google_oauth2_client = GoogleOAuth2(
    client_id=settings.app.GOOGLE_OAUTH2_CLIENT_ID, client_secret=settings.app.GOOGLE_OAUTH2_CLIENT_SECRET,
)

from __future__ import annotations

from httpx_oauth.clients.github import GitHubOAuth2
from httpx_oauth.clients.google import GoogleOAuth2

from app.lib.settings import get_settings

_settings = get_settings()

# Framework configs via get_config() methods
compression = _settings.app.get_compression_config()
csrf = _settings.app.get_csrf_config()
cors = _settings.app.get_cors_config()
session = _settings.app.get_session_config()
templates = _settings.app.get_template_config(_settings.vite.TEMPLATE_DIR)
alchemy = _settings.db.get_config()
vite = _settings.vite.get_config(_settings.app)
log = _settings.log.get_structlog_config()
email = _settings.email.get_email_config()
# OAuth clients
github_oauth2_client = GitHubOAuth2(
    client_id=_settings.app.GITHUB_OAUTH2_CLIENT_ID, client_secret=_settings.app.GITHUB_OAUTH2_CLIENT_SECRET,
)
google_oauth2_client = GoogleOAuth2(
    client_id=_settings.app.GOOGLE_OAUTH2_CLIENT_ID, client_secret=_settings.app.GOOGLE_OAUTH2_CLIENT_SECRET,
)

# Configure storage
_settings.storage.configure_storage()

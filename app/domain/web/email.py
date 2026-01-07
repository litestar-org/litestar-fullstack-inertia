"""Email service for sending transactional emails.

This module provides the EmailMessageService class which offers a high-level
API for sending various types of transactional emails including
verification, password reset, welcome, and team invitation emails.

It uses litestar-email's EmailService for actual email delivery and
includes a simple template renderer with {{PLACEHOLDER}} syntax.
"""

from __future__ import annotations

import html
import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol
from urllib.parse import quote

from litestar_email import EmailMultiAlternatives

from app.lib.settings import get_settings

if TYPE_CHECKING:
    from litestar_email import EmailService

logger = logging.getLogger(__name__)

# Template directory for email templates
TEMPLATE_DIR = Path(__file__).parent / "templates" / "email"

# Pattern for placeholder matching: {{VARIABLE_NAME}}
PLACEHOLDER_PATTERN = re.compile(r"\{\{(\w+)\}\}")

# Pattern for stripping HTML tags for plain text fallback
HTML_TAG_PATTERN = re.compile(r"<[^<]+?>")


class TemplateRenderer:
    """Renders pre-built email templates with data injection.

    Uses simple placeholder replacement instead of Jinja2.
    Placeholders use {{VARIABLE_NAME}} syntax.
    """

    def __init__(self, template_dir: Path | None = None) -> None:
        """Initialize the template renderer.

        Args:
            template_dir: Directory containing template files.
        """
        self.template_dir = template_dir or TEMPLATE_DIR
        self._cache: dict[str, str] = {}

    def render(self, template_name: str, context: dict[str, Any]) -> str:
        """Render a template with the given context.

        Placeholders in the template are replaced with values from the
        context dictionary. Values are HTML-escaped for security.

        Args:
            template_name: Name of template file (without extension).
            context: Dictionary of values to inject into placeholders.

        Returns:
            Rendered HTML string.

        Raises:
            FileNotFoundError: If template file does not exist.
        """
        template = self._load_template(template_name)

        def replace_placeholder(match: re.Match[str]) -> str:
            key = match.group(1)
            value = context.get(key)
            if value is None:
                return f"{{{{MISSING:{key}}}}}"
            return html.escape(str(value), quote=True)

        return PLACEHOLDER_PATTERN.sub(replace_placeholder, template)

    def render_unsafe(self, template_name: str, context: dict[str, Any]) -> str:
        """Render a template without HTML escaping.

        Use this only when context values are already safe HTML.
        """
        template = self._load_template(template_name)

        def replace_placeholder(match: re.Match[str]) -> str:
            key = match.group(1)
            value = context.get(key)
            if value is None:
                return f"{{{{MISSING:{key}}}}}"
            return str(value)

        return PLACEHOLDER_PATTERN.sub(replace_placeholder, template)

    def _load_template(self, template_name: str) -> str:
        """Load template from file or cache."""
        if template_name not in self._cache:
            template_path = self.template_dir / f"{template_name}.html"
            if not template_path.exists():
                msg = f"Email template not found: {template_path}"
                raise FileNotFoundError(msg)
            self._cache[template_name] = template_path.read_text(encoding="utf-8")
        return self._cache[template_name]

    def template_exists(self, template_name: str) -> bool:
        """Check if a template exists."""
        template_path = self.template_dir / f"{template_name}.html"
        return template_path.exists()

    def clear_cache(self) -> None:
        """Clear template cache."""
        self._cache.clear()


@lru_cache(maxsize=1)
def get_template_renderer() -> TemplateRenderer:
    """Get the global template renderer instance."""
    return TemplateRenderer()


class UserProtocol(Protocol):
    """Protocol for User objects used in email methods."""

    email: str
    name: str | None


class EmailMessageService:
    """High-level service for sending transactional emails.

    This service provides methods for sending various types of emails
    including verification, password reset, welcome, and invitation emails.

    Uses litestar-email's EmailService for actual delivery.

    Example:
        # In a signal handler (outside request context)
        from app import config

        async with config.email.provide_service() as mailer:
            service = EmailMessageService(mailer=mailer)
            await service.send_verification_email(user, token)

        # In a route handler (with dependency injection)
        service = EmailMessageService(mailer=mailer)  # mailer injected
        await service.send_verification_email(user, token)
    """

    def __init__(
        self,
        mailer: EmailService,
        renderer: TemplateRenderer | None = None,
        fail_silently: bool = False,
    ) -> None:
        """Initialize the email message service.

        Args:
            mailer: The litestar-email EmailService instance.
            renderer: Template renderer to use. If None, uses default.
            fail_silently: If True, suppress exceptions during send.
        """
        self.mailer = mailer
        self.renderer = renderer or get_template_renderer()
        self.fail_silently = fail_silently
        self._settings = get_settings()

    @property
    def app_name(self) -> str:
        """Get application name from settings."""
        return self._settings.app.NAME

    @property
    def base_url(self) -> str:
        """Get base URL from settings."""
        return self._settings.app.URL

    async def send_email(
        self,
        to_email: str | list[str],
        subject: str,
        html_content: str,
        text_content: str | None = None,
        from_email: str | None = None,
        reply_to: str | None = None,
    ) -> bool:
        """Send an email with HTML and optional text content.

        Args:
            to_email: Recipient email address(es).
            subject: Email subject.
            html_content: HTML email content.
            text_content: Plain text content (generated from HTML if not provided).
            from_email: Sender email (uses default if not provided).
            reply_to: Reply-to email address.

        Returns:
            True if email was sent successfully, False otherwise.
        """
        if not self._settings.email.ENABLED:
            logger.info("Email service disabled. Would send email to %s with subject: %s", to_email, subject)
            return False

        # Generate plain text from HTML if not provided
        if not text_content:
            text_content = self._html_to_text(html_content)

        # Normalize recipients to list
        recipients = [to_email] if isinstance(to_email, str) else to_email

        message = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            html_body=html_content,
            from_email=from_email,
            to=recipients,
            reply_to=[reply_to] if reply_to else [],
        )

        try:
            await self.mailer.send_message(message)
        except Exception:
            logger.exception("Failed to send email to %s", to_email)
            if not self.fail_silently:
                raise
            return False
        else:
            return True

    async def send_template_email(
        self,
        template_name: str,
        to_email: str | list[str],
        subject: str,
        context: dict[str, Any],
        from_email: str | None = None,
    ) -> bool:
        """Send email using a template.

        If the template doesn't exist, falls back to the provided context
        values for generating a simple HTML email.

        Args:
            template_name: Name of template file (without extension).
            to_email: Recipient email address(es).
            subject: Email subject.
            context: Template context variables.
            from_email: Sender email (uses default if not provided).

        Returns:
            True if email was sent successfully, False otherwise.
        """
        try:
            if self.renderer.template_exists(template_name):
                html_content = self.renderer.render(template_name, context)
            else:
                logger.debug("Template %s not found, using fallback", template_name)
                html_content = self._generate_fallback_html(template_name, context)

            return await self.send_email(
                to_email=to_email, subject=subject, html_content=html_content, from_email=from_email,
            )

        except Exception:
            logger.exception("Failed to send template email %s", template_name)
            if not self.fail_silently:
                raise
            return False

    async def send_verification_email(self, user: UserProtocol, token: str) -> bool:
        """Send email verification email to user."""
        verification_url = f"{self.base_url}/verify-email?token={token}"

        context = {
            "APP_NAME": self.app_name,
            "USER_NAME": user.name or "there",
            "USER_EMAIL": user.email,
            "VERIFICATION_URL": verification_url,
            "EXPIRES_HOURS": self._settings.email.VERIFICATION_TOKEN_EXPIRES_HOURS,
        }

        return await self.send_template_email(
            template_name="email-verification",
            to_email=user.email,
            subject=f"Verify your email address for {self.app_name}",
            context=context,
        )

    async def send_welcome_email(self, user: UserProtocol) -> bool:
        """Send welcome email to newly verified user."""
        context = {
            "APP_NAME": self.app_name,
            "USER_NAME": user.name or "there",
            "USER_EMAIL": user.email,
            "LOGIN_URL": f"{self.base_url}/login",
        }

        return await self.send_template_email(
            template_name="welcome", to_email=user.email, subject=f"Welcome to {self.app_name}!", context=context,
        )

    async def send_password_reset_email(self, user: UserProtocol, token: str, ip_address: str = "unknown") -> bool:
        """Send password reset email to user."""
        reset_url = f"{self.base_url}/reset-password?token={token}&email={quote(user.email)}"
        expires_minutes = self._settings.email.PASSWORD_RESET_TOKEN_EXPIRES_MINUTES

        context = {
            "APP_NAME": self.app_name,
            "USER_NAME": user.name or "there",
            "USER_EMAIL": user.email,
            "RESET_URL": reset_url,
            "EXPIRES_MINUTES": expires_minutes,
            "IP_ADDRESS": ip_address,
        }

        return await self.send_template_email(
            template_name="password-reset",
            to_email=user.email,
            subject=f"Reset your password for {self.app_name}",
            context=context,
        )

    async def send_password_reset_confirmation_email(self, user: UserProtocol) -> bool:
        """Send password reset confirmation email to user."""
        context = {
            "APP_NAME": self.app_name,
            "USER_NAME": user.name or "there",
            "USER_EMAIL": user.email,
            "LOGIN_URL": f"{self.base_url}/login",
        }

        return await self.send_template_email(
            template_name="password-reset-confirmation",
            to_email=user.email,
            subject=f"Your password has been reset for {self.app_name}",
            context=context,
        )

    async def send_team_invitation_email(
        self, invitee_email: str, inviter_name: str, team_name: str, token: str,
    ) -> bool:
        """Send team invitation email."""
        invitation_url = f"{self.base_url}/invitations/{token}/"

        context = {
            "APP_NAME": self.app_name,
            "INVITER_NAME": inviter_name,
            "TEAM_NAME": team_name,
            "INVITATION_URL": invitation_url,
            "EXPIRES_DAYS": self._settings.email.INVITATION_TOKEN_EXPIRES_DAYS,
        }

        return await self.send_template_email(
            template_name="team-invitation",
            to_email=invitee_email,
            subject=f"{inviter_name} invited you to join {team_name} on {self.app_name}",
            context=context,
        )

    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML to plain text."""
        text = HTML_TAG_PATTERN.sub("", html_content)
        text = text.replace("&nbsp;", " ")
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _generate_fallback_html(self, template_name: str, context: dict[str, Any]) -> str:
        """Generate fallback HTML when template is not found."""
        app_name = context.get("APP_NAME", self.app_name)
        user_name = context.get("USER_NAME", "there")
        primary = "#202235"
        accent = "#EDB641"
        surface = "#ffffff"
        border = "#DCDFE4"

        if "verification" in template_name:
            url = context.get("VERIFICATION_URL", "")
            expires = context.get("EXPIRES_HOURS", 24)
            content = f"""
                <p>Hi {user_name},</p>
                <p>Please verify your email address by clicking the link below:</p>
                <p><a href="{url}" style="display: inline-block; padding: 10px 20px;
                    background-color: {accent}; color: {primary}; text-decoration: none;
                    border-radius: 4px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;">Verify Email</a></p>
                <p>Or copy and paste this URL: {url}</p>
                <p>This link expires in {expires} hours.</p>
            """
        elif "reset" in template_name and "confirmation" not in template_name:
            url = context.get("RESET_URL", "")
            expires = context.get("EXPIRES_MINUTES", 60)
            content = f"""
                <p>Hi {user_name},</p>
                <p>You requested to reset your password. Click the link below:</p>
                <p><a href="{url}" style="display: inline-block; padding: 10px 20px;
                    background-color: {accent}; color: {primary}; text-decoration: none;
                    border-radius: 4px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;">Reset Password</a></p>
                <p>Or copy and paste this URL: {url}</p>
                <p>This link expires in {expires} minutes.</p>
                <p>If you didn't request this, please ignore this email.</p>
            """
        elif "confirmation" in template_name:
            url = context.get("LOGIN_URL", "")
            content = f"""
                <p>Hi {user_name},</p>
                <p>Your password has been successfully reset.</p>
                <p><a href="{url}" style="display: inline-block; padding: 10px 20px;
                    background-color: {accent}; color: {primary}; text-decoration: none;
                    border-radius: 4px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;">Log In</a></p>
                <p>If you didn't make this change, contact support immediately.</p>
            """
        elif "welcome" in template_name:
            url = context.get("LOGIN_URL", "")
            content = f"""
                <p>Hi {user_name},</p>
                <p>Welcome to {app_name}! Your account is now active.</p>
                <p><a href="{url}" style="display: inline-block; padding: 10px 20px;
                    background-color: {accent}; color: {primary}; text-decoration: none;
                    border-radius: 4px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;">Log In</a></p>
            """
        elif "invitation" in template_name:
            url = context.get("INVITATION_URL", "")
            inviter = context.get("INVITER_NAME", "Someone")
            team = context.get("TEAM_NAME", "a team")
            expires = context.get("EXPIRES_DAYS", 7)
            content = f"""
                <p>Hi there,</p>
                <p>{inviter} has invited you to join {team} on {app_name}.</p>
                <p><a href="{url}" style="display: inline-block; padding: 10px 20px;
                    background-color: {accent}; color: {primary}; text-decoration: none;
                    border-radius: 4px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;">Accept Invitation</a></p>
                <p>Or copy and paste this URL: {url}</p>
                <p>This invitation expires in {expires} days.</p>
            """
        else:
            content = f"""
                <p>Hi {user_name},</p>
                <p>This is a message from {app_name}.</p>
            """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                     line-height: 1.6; color: {primary}; background: {border};
                     max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: {primary}; color: white; padding: 20px; text-align: center;">
                <h1 style="margin: 0;">{app_name}</h1>
            </div>
            <div style="background: {surface}; padding: 30px; border: 1px solid {border};">
                {content}
            </div>
            <div style="text-align: center; padding: 20px; font-size: 12px; color: {primary};">
                <p>&copy; {app_name}</p>
            </div>
        </body>
        </html>
        """

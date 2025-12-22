"""High-level email service.

This module provides the EmailService class which offers a high-level
API for sending various types of transactional emails including
verification, password reset, welcome, and team invitation emails.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Protocol

from app.lib.email.backends import get_backend
from app.lib.email.base import EmailMultiAlternatives
from app.lib.email.renderer import TemplateRenderer, get_template_renderer
from app.lib.settings import get_settings

logger = logging.getLogger(__name__)

# Pattern for stripping HTML tags for plain text fallback
HTML_TAG_PATTERN = re.compile(r"<[^<]+?>")


class UserProtocol(Protocol):
    """Protocol for User objects used in email methods."""

    email: str
    name: str | None


class EmailService:
    """High-level service for sending transactional emails.

    This service provides methods for sending various types of emails
    including verification, password reset, welcome, and invitation emails.

    The service uses the configured email backend and template renderer
    for flexible email delivery.

    Example:
        service = EmailService()
        await service.send_verification_email(user, token)
        await service.send_password_reset_email(user, token)
    """

    def __init__(self, renderer: TemplateRenderer | None = None, fail_silently: bool = False) -> None:
        """Initialize the email service.

        Args:
            renderer: Template renderer to use. If None, uses default.
            fail_silently: If True, suppress exceptions during send.
        """
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
            backend = get_backend(fail_silently=self.fail_silently)
            num_sent = await backend.send_messages([message])
        except Exception:
            logger.exception("Failed to send email to %s", to_email)
            if not self.fail_silently:
                raise
            return False
        else:
            return num_sent > 0

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
        """Send email verification email to user.

        Args:
            user: The user to send the email to.
            token: The verification token.

        Returns:
            True if email was sent successfully.
        """
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
        """Send welcome email to newly verified user.

        Args:
            user: The user to send the welcome email to.

        Returns:
            True if email was sent successfully.
        """
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
        """Send password reset email to user.

        Args:
            user: The user to send the email to.
            token: The password reset token.
            ip_address: IP address where reset was requested.

        Returns:
            True if email was sent successfully.
        """
        reset_url = f"{self.base_url}/reset-password?token={token}"
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
        """Send password reset confirmation email to user.

        Args:
            user: The user whose password was reset.

        Returns:
            True if email was sent successfully.
        """
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
        """Send team invitation email.

        Args:
            invitee_email: Email address to send invitation to.
            inviter_name: Name of person sending invitation.
            team_name: Name of the team.
            token: Invitation token.

        Returns:
            True if email was sent successfully.
        """
        invitation_url = f"{self.base_url}/invitations/{token}/accept"

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
        """Convert HTML to plain text.

        Args:
            html_content: HTML string to convert.

        Returns:
            Plain text string.
        """
        text = HTML_TAG_PATTERN.sub("", html_content)
        text = text.replace("&nbsp;", " ")
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _generate_fallback_html(self, template_name: str, context: dict[str, Any]) -> str:
        """Generate fallback HTML when template is not found.

        Args:
            template_name: Name of the template that was not found.
            context: Template context variables.

        Returns:
            Simple HTML email content.
        """
        app_name = context.get("APP_NAME", self.app_name)
        user_name = context.get("USER_NAME", "there")
        primary = "#202235"
        accent = "#EDB641"
        surface = "#ffffff"
        border = "#DCDFE4"

        # Generate content based on template type
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

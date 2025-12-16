"""Tests for email service."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.lib.email.backends.locmem import InMemoryBackend
from app.lib.email.service import EmailService

if TYPE_CHECKING:
    from tests.unit.lib.email.conftest import MockUser

pytestmark = pytest.mark.anyio


@pytest.fixture
def email_service() -> EmailService:
    """Create an email service instance for testing."""
    return EmailService(fail_silently=True)


@pytest.fixture
def mock_settings() -> MagicMock:
    """Create mock settings for testing."""
    settings = MagicMock()
    settings.app.NAME = "TestApp"
    settings.app.URL = "http://test.example.com"
    settings.email.ENABLED = True
    settings.email.BACKEND = "locmem"
    settings.email.FROM_EMAIL = "test@example.com"
    settings.email.VERIFICATION_TOKEN_EXPIRES_HOURS = 24
    settings.email.PASSWORD_RESET_TOKEN_EXPIRES_MINUTES = 60
    settings.email.INVITATION_TOKEN_EXPIRES_DAYS = 7
    return settings


@pytest.mark.usefixtures("clear_email_outbox")
async def test_send_email_basic(mock_settings: MagicMock) -> None:
    """Test basic email sending."""
    with patch("app.lib.email.service.get_settings", return_value=mock_settings), \
         patch("app.lib.email.service.get_backend") as mock_get_backend:

        mock_backend = InMemoryBackend()
        mock_get_backend.return_value = mock_backend

        service = EmailService()
        result = await service.send_email(
            to_email="recipient@example.com",
            subject="Test Subject",
            html_content="<p>Test content</p>",
        )

        assert result is True
        assert len(InMemoryBackend.outbox) == 1
        assert InMemoryBackend.outbox[0].subject == "Test Subject"


@pytest.mark.usefixtures("clear_email_outbox")
async def test_send_email_when_disabled(mock_settings: MagicMock) -> None:
    """Test that email is not sent when disabled."""
    mock_settings.email.ENABLED = False

    with patch("app.lib.email.service.get_settings", return_value=mock_settings):
        service = EmailService()
        result = await service.send_email(
            to_email="recipient@example.com",
            subject="Test",
            html_content="<p>Test</p>",
        )

        assert result is False
        assert len(InMemoryBackend.outbox) == 0


async def test_send_email_list_recipients(mock_settings: MagicMock) -> None:
    """Test sending email to multiple recipients."""
    with patch("app.lib.email.service.get_settings", return_value=mock_settings), \
         patch("app.lib.email.service.get_backend") as mock_get_backend:

        mock_backend = InMemoryBackend()
        mock_get_backend.return_value = mock_backend
        InMemoryBackend.clear()

        service = EmailService()
        await service.send_email(
            to_email=["one@example.com", "two@example.com"],
            subject="Multi",
            html_content="<p>Content</p>",
        )

        assert len(InMemoryBackend.outbox) == 1
        assert InMemoryBackend.outbox[0].to == ["one@example.com", "two@example.com"]


async def test_send_email_html_to_text_conversion(mock_settings: MagicMock) -> None:
    """Test HTML to text conversion."""
    with patch("app.lib.email.service.get_settings", return_value=mock_settings), \
         patch("app.lib.email.service.get_backend") as mock_get_backend:

        mock_backend = InMemoryBackend()
        mock_get_backend.return_value = mock_backend
        InMemoryBackend.clear()

        service = EmailService()
        await service.send_email(
            to_email="test@example.com",
            subject="Test",
            html_content="<p>Hello <strong>World</strong></p>",
        )

        message = InMemoryBackend.outbox[0]
        assert message.body == "Hello World"  # HTML stripped


async def test_send_template_email(mock_settings: MagicMock) -> None:
    """Test sending email using template."""
    with patch("app.lib.email.service.get_settings", return_value=mock_settings), \
         patch("app.lib.email.service.get_backend") as mock_get_backend:

        mock_backend = InMemoryBackend()
        mock_get_backend.return_value = mock_backend
        InMemoryBackend.clear()

        mock_renderer = MagicMock()
        mock_renderer.template_exists.return_value = True
        mock_renderer.render.return_value = "<p>Rendered content</p>"

        service = EmailService(renderer=mock_renderer)
        result = await service.send_template_email(
            template_name="test",
            to_email="test@example.com",
            subject="Template Test",
            context={"key": "value"},
        )

        assert result is True
        mock_renderer.render.assert_called_once_with("test", {"key": "value"})


async def test_send_template_email_fallback(mock_settings: MagicMock) -> None:
    """Test template email with fallback when template not found."""
    with patch("app.lib.email.service.get_settings", return_value=mock_settings), \
         patch("app.lib.email.service.get_backend") as mock_get_backend:

        mock_backend = InMemoryBackend()
        mock_get_backend.return_value = mock_backend
        InMemoryBackend.clear()

        mock_renderer = MagicMock()
        mock_renderer.template_exists.return_value = False

        service = EmailService(renderer=mock_renderer)
        result = await service.send_template_email(
            template_name="nonexistent",
            to_email="test@example.com",
            subject="Fallback Test",
            context={"APP_NAME": "Test", "USER_NAME": "Bob"},
        )

        assert result is True
        # Fallback HTML should be generated
        assert len(InMemoryBackend.outbox) == 1


@pytest.mark.usefixtures("clear_email_outbox")
async def test_send_verification_email(mock_user: "MockUser", mock_settings: MagicMock) -> None:
    """Test sending verification email."""
    with patch("app.lib.email.service.get_settings", return_value=mock_settings), \
         patch("app.lib.email.service.get_backend") as mock_get_backend:

        mock_backend = InMemoryBackend()
        mock_get_backend.return_value = mock_backend

        mock_renderer = MagicMock()
        mock_renderer.template_exists.return_value = True
        mock_renderer.render.return_value = "<p>Verify</p>"

        service = EmailService(renderer=mock_renderer)
        result = await service.send_verification_email(mock_user, "token123")

        assert result is True
        mock_renderer.render.assert_called_once()
        call_args = mock_renderer.render.call_args
        assert call_args[0][0] == "email-verification"
        assert "VERIFICATION_URL" in call_args[0][1]
        assert "token123" in call_args[0][1]["VERIFICATION_URL"]


@pytest.mark.usefixtures("clear_email_outbox")
async def test_send_password_reset_email(mock_user: "MockUser", mock_settings: MagicMock) -> None:
    """Test sending password reset email."""
    with patch("app.lib.email.service.get_settings", return_value=mock_settings), \
         patch("app.lib.email.service.get_backend") as mock_get_backend:

        mock_backend = InMemoryBackend()
        mock_get_backend.return_value = mock_backend

        mock_renderer = MagicMock()
        mock_renderer.template_exists.return_value = True
        mock_renderer.render.return_value = "<p>Reset</p>"

        service = EmailService(renderer=mock_renderer)
        result = await service.send_password_reset_email(
            mock_user, "reset-token", ip_address="192.168.1.1",
        )

        assert result is True
        call_args = mock_renderer.render.call_args
        assert call_args[0][0] == "password-reset"
        assert "reset-token" in call_args[0][1]["RESET_URL"]
        assert call_args[0][1]["IP_ADDRESS"] == "192.168.1.1"


@pytest.mark.usefixtures("clear_email_outbox")
async def test_send_welcome_email(mock_user: "MockUser", mock_settings: MagicMock) -> None:
    """Test sending welcome email."""
    with patch("app.lib.email.service.get_settings", return_value=mock_settings), \
         patch("app.lib.email.service.get_backend") as mock_get_backend:

        mock_backend = InMemoryBackend()
        mock_get_backend.return_value = mock_backend

        mock_renderer = MagicMock()
        mock_renderer.template_exists.return_value = True
        mock_renderer.render.return_value = "<p>Welcome</p>"

        service = EmailService(renderer=mock_renderer)
        result = await service.send_welcome_email(mock_user)

        assert result is True
        call_args = mock_renderer.render.call_args
        assert call_args[0][0] == "welcome"


@pytest.mark.usefixtures("clear_email_outbox")
async def test_send_team_invitation_email(mock_settings: MagicMock) -> None:
    """Test sending team invitation email."""
    with patch("app.lib.email.service.get_settings", return_value=mock_settings), \
         patch("app.lib.email.service.get_backend") as mock_get_backend:

        mock_backend = InMemoryBackend()
        mock_get_backend.return_value = mock_backend

        mock_renderer = MagicMock()
        mock_renderer.template_exists.return_value = True
        mock_renderer.render.return_value = "<p>Invitation</p>"

        service = EmailService(renderer=mock_renderer)
        result = await service.send_team_invitation_email(
            invitee_email="new@example.com",
            inviter_name="Alice",
            team_name="Team Alpha",
            token="invite-token",
        )

        assert result is True
        call_args = mock_renderer.render.call_args
        assert call_args[0][0] == "team-invitation"
        assert call_args[0][1]["INVITER_NAME"] == "Alice"
        assert call_args[0][1]["TEAM_NAME"] == "Team Alpha"
        assert "invite-token" in call_args[0][1]["INVITATION_URL"]


def test_html_to_text_basic() -> None:
    """Test HTML to text conversion with basic HTML."""
    service = EmailService()
    result = service._html_to_text("<p>Hello <b>World</b></p>")
    assert result == "Hello World"


def test_html_to_text_entities() -> None:
    """Test HTML to text conversion with HTML entities."""
    service = EmailService()
    result = service._html_to_text("&nbsp;&amp;&lt;&gt;&quot;")
    # _html_to_text converts common entities: &nbsp;-> space, &amp;->&, etc
    assert "&" in result
    assert "<" in result
    assert ">" in result


def test_html_to_text_whitespace() -> None:
    """Test HTML to text conversion collapses whitespace."""
    service = EmailService()
    result = service._html_to_text("<p>  Hello   World  </p>")
    assert result == "Hello World"


def test_app_name_property(mock_settings: MagicMock) -> None:
    """Test app_name property returns correct value."""
    with patch("app.lib.email.service.get_settings", return_value=mock_settings):
        service = EmailService()
        assert service.app_name == "TestApp"


def test_base_url_property(mock_settings: MagicMock) -> None:
    """Test base_url property returns correct value."""
    with patch("app.lib.email.service.get_settings", return_value=mock_settings):
        service = EmailService()
        assert service.base_url == "http://test.example.com"


async def test_send_email_exception_with_fail_silently(mock_settings: MagicMock) -> None:
    """Test that exceptions are suppressed with fail_silently=True."""
    mock_settings.email.ENABLED = True

    with patch("app.lib.email.service.get_settings", return_value=mock_settings), \
         patch("app.lib.email.service.get_backend") as mock_get_backend:

        mock_backend = AsyncMock()
        mock_backend.send_messages.side_effect = Exception("SMTP Error")
        mock_get_backend.return_value = mock_backend

        service = EmailService(fail_silently=True)
        result = await service.send_email(
            to_email="test@example.com",
            subject="Test",
            html_content="<p>Test</p>",
        )

        assert result is False


async def test_send_email_exception_without_fail_silently(mock_settings: MagicMock) -> None:
    """Test that exceptions are raised with fail_silently=False."""
    mock_settings.email.ENABLED = True

    with patch("app.lib.email.service.get_settings", return_value=mock_settings), \
         patch("app.lib.email.service.get_backend") as mock_get_backend:

        mock_backend = AsyncMock()
        mock_backend.send_messages.side_effect = Exception("SMTP Error")
        mock_get_backend.return_value = mock_backend

        service = EmailService(fail_silently=False)
        with pytest.raises(Exception, match="SMTP Error"):
            await service.send_email(
                to_email="test@example.com",
                subject="Test",
                html_content="<p>Test</p>",
            )

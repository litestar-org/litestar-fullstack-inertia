"""Tests for email module (service and renderer)."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domain.web.email import EmailMessageService, TemplateRenderer, get_template_renderer

if TYPE_CHECKING:
    from collections.abc import Generator

    from tests.unit.domain.web.conftest import MockUser

pytestmark = pytest.mark.anyio


# ============================================================================
# Template Renderer Tests
# ============================================================================


@pytest.fixture
def temp_template_dir() -> Generator[Path, None, None]:
    """Create a temporary directory with test templates."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create a test template
        (tmppath / "test-template.html").write_text(
            "<h1>Hello {{USER_NAME}}</h1><p>Your code is {{CODE}}</p>",
        )

        # Create template with special characters
        (tmppath / "special-chars.html").write_text(
            "<p>{{CONTENT}}</p>",
        )

        yield tmppath


def test_render_template_basic(temp_template_dir: Path) -> None:
    """Test basic template rendering with placeholder substitution."""
    renderer = TemplateRenderer(template_dir=temp_template_dir)

    result = renderer.render("test-template", {
        "USER_NAME": "Alice",
        "CODE": "12345",
    })

    assert "<h1>Hello Alice</h1>" in result
    assert "Your code is 12345" in result


def test_render_escapes_html(temp_template_dir: Path) -> None:
    """Test that template rendering escapes HTML special characters."""
    renderer = TemplateRenderer(template_dir=temp_template_dir)

    result = renderer.render("special-chars", {
        "CONTENT": "<script>alert('xss')</script>",
    })

    assert "&lt;script&gt;" in result
    assert "<script>" not in result


def test_render_unsafe_does_not_escape(temp_template_dir: Path) -> None:
    """Test render_unsafe does not escape HTML."""
    renderer = TemplateRenderer(template_dir=temp_template_dir)

    result = renderer.render_unsafe("special-chars", {
        "CONTENT": "<strong>Bold</strong>",
    })

    assert "<strong>Bold</strong>" in result


def test_render_missing_placeholder_marker(temp_template_dir: Path) -> None:
    """Test that missing placeholders are marked in output."""
    renderer = TemplateRenderer(template_dir=temp_template_dir)

    result = renderer.render("test-template", {
        "USER_NAME": "Bob",
        # CODE is missing
    })

    assert "Hello Bob" in result
    assert "{{MISSING:CODE}}" in result


def test_render_nonexistent_template_raises(temp_template_dir: Path) -> None:
    """Test that rendering nonexistent template raises FileNotFoundError."""
    renderer = TemplateRenderer(template_dir=temp_template_dir)

    with pytest.raises(FileNotFoundError):
        renderer.render("nonexistent", {})


def test_template_exists_true(temp_template_dir: Path) -> None:
    """Test template_exists returns True for existing template."""
    renderer = TemplateRenderer(template_dir=temp_template_dir)
    assert renderer.template_exists("test-template") is True


def test_template_exists_false(temp_template_dir: Path) -> None:
    """Test template_exists returns False for nonexistent template."""
    renderer = TemplateRenderer(template_dir=temp_template_dir)
    assert renderer.template_exists("nonexistent") is False


def test_template_caching(temp_template_dir: Path) -> None:
    """Test that templates are cached after first load."""
    renderer = TemplateRenderer(template_dir=temp_template_dir)

    # First render loads template
    renderer.render("test-template", {"USER_NAME": "First", "CODE": "111"})
    assert "test-template" in renderer._cache

    # Modify the file
    (temp_template_dir / "test-template.html").write_text("<p>Modified</p>")

    # Second render uses cache
    result = renderer.render("test-template", {"USER_NAME": "Second", "CODE": "222"})
    assert "Hello" in result  # Original content, not "Modified"


def test_clear_cache(temp_template_dir: Path) -> None:
    """Test that clear_cache removes cached templates."""
    renderer = TemplateRenderer(template_dir=temp_template_dir)

    # Load template
    renderer.render("test-template", {"USER_NAME": "Test", "CODE": "000"})
    assert "test-template" in renderer._cache

    # Clear cache
    renderer.clear_cache()
    assert len(renderer._cache) == 0


def test_get_template_renderer_returns_cached_instance() -> None:
    """Test get_template_renderer returns the same instance."""
    renderer1 = get_template_renderer()
    renderer2 = get_template_renderer()
    assert renderer1 is renderer2


def test_render_with_numeric_values(temp_template_dir: Path) -> None:
    """Test rendering with non-string values."""
    renderer = TemplateRenderer(template_dir=temp_template_dir)

    result = renderer.render("test-template", {
        "USER_NAME": "Numbers",
        "CODE": 42,
    })

    assert "42" in result


# ============================================================================
# Email Message Service Tests
# ============================================================================


@pytest.fixture
def mock_settings() -> MagicMock:
    """Create mock settings for testing."""
    settings = MagicMock()
    settings.app.NAME = "TestApp"
    settings.app.URL = "http://test.example.com"
    settings.email.ENABLED = True
    settings.email.BACKEND = "memory"
    settings.email.FROM_EMAIL = "test@example.com"
    settings.email.VERIFICATION_TOKEN_EXPIRES_HOURS = 24
    settings.email.PASSWORD_RESET_TOKEN_EXPIRES_MINUTES = 60
    settings.email.INVITATION_TOKEN_EXPIRES_DAYS = 7
    return settings


async def test_send_email_basic(mock_mailer: AsyncMock, mock_settings: MagicMock) -> None:
    """Test basic email sending."""
    with patch("app.domain.web.email.get_settings", return_value=mock_settings):
        service = EmailMessageService(mailer=mock_mailer)
        result = await service.send_email(
            to_email="recipient@example.com",
            subject="Test Subject",
            html_content="<p>Test content</p>",
        )

        assert result is True
        mock_mailer.send_message.assert_called_once()


async def test_send_email_when_disabled(mock_mailer: AsyncMock, mock_settings: MagicMock) -> None:
    """Test that email is not sent when disabled."""
    mock_settings.email.ENABLED = False

    with patch("app.domain.web.email.get_settings", return_value=mock_settings):
        service = EmailMessageService(mailer=mock_mailer)
        result = await service.send_email(
            to_email="recipient@example.com",
            subject="Test",
            html_content="<p>Test</p>",
        )

        assert result is False
        mock_mailer.send_message.assert_not_called()


async def test_send_email_list_recipients(mock_mailer: AsyncMock, mock_settings: MagicMock) -> None:
    """Test sending email to multiple recipients."""
    with patch("app.domain.web.email.get_settings", return_value=mock_settings):
        service = EmailMessageService(mailer=mock_mailer)
        await service.send_email(
            to_email=["one@example.com", "two@example.com"],
            subject="Multi",
            html_content="<p>Content</p>",
        )

        call_args = mock_mailer.send_message.call_args
        message = call_args[0][0]
        assert message.to == ["one@example.com", "two@example.com"]


async def test_send_email_html_to_text_conversion(mock_mailer: AsyncMock, mock_settings: MagicMock) -> None:
    """Test HTML to text conversion."""
    with patch("app.domain.web.email.get_settings", return_value=mock_settings):
        service = EmailMessageService(mailer=mock_mailer)
        await service.send_email(
            to_email="test@example.com",
            subject="Test",
            html_content="<p>Hello <strong>World</strong></p>",
        )

        call_args = mock_mailer.send_message.call_args
        message = call_args[0][0]
        assert message.body == "Hello World"  # HTML stripped


async def test_send_template_email(mock_mailer: AsyncMock, mock_settings: MagicMock) -> None:
    """Test sending email using template."""
    with patch("app.domain.web.email.get_settings", return_value=mock_settings):
        mock_renderer = MagicMock()
        mock_renderer.template_exists.return_value = True
        mock_renderer.render.return_value = "<p>Rendered content</p>"

        service = EmailMessageService(mailer=mock_mailer, renderer=mock_renderer)
        result = await service.send_template_email(
            template_name="test",
            to_email="test@example.com",
            subject="Template Test",
            context={"key": "value"},
        )

        assert result is True
        mock_renderer.render.assert_called_once_with("test", {"key": "value"})


async def test_send_template_email_fallback(mock_mailer: AsyncMock, mock_settings: MagicMock) -> None:
    """Test template email with fallback when template not found."""
    with patch("app.domain.web.email.get_settings", return_value=mock_settings):
        mock_renderer = MagicMock()
        mock_renderer.template_exists.return_value = False

        service = EmailMessageService(mailer=mock_mailer, renderer=mock_renderer)
        result = await service.send_template_email(
            template_name="nonexistent",
            to_email="test@example.com",
            subject="Fallback Test",
            context={"APP_NAME": "Test", "USER_NAME": "Bob"},
        )

        assert result is True
        # Fallback HTML should be generated
        mock_mailer.send_message.assert_called_once()


async def test_send_verification_email(
    mock_user: "MockUser", mock_mailer: AsyncMock, mock_settings: MagicMock,
) -> None:
    """Test sending verification email."""
    with patch("app.domain.web.email.get_settings", return_value=mock_settings):
        mock_renderer = MagicMock()
        mock_renderer.template_exists.return_value = True
        mock_renderer.render.return_value = "<p>Verify</p>"

        service = EmailMessageService(mailer=mock_mailer, renderer=mock_renderer)
        result = await service.send_verification_email(mock_user, "token123")

        assert result is True
        mock_renderer.render.assert_called_once()
        call_args = mock_renderer.render.call_args
        assert call_args[0][0] == "email-verification"
        assert "VERIFICATION_URL" in call_args[0][1]
        assert "token123" in call_args[0][1]["VERIFICATION_URL"]


async def test_send_password_reset_email(
    mock_user: "MockUser", mock_mailer: AsyncMock, mock_settings: MagicMock,
) -> None:
    """Test sending password reset email."""
    with patch("app.domain.web.email.get_settings", return_value=mock_settings):
        mock_renderer = MagicMock()
        mock_renderer.template_exists.return_value = True
        mock_renderer.render.return_value = "<p>Reset</p>"

        service = EmailMessageService(mailer=mock_mailer, renderer=mock_renderer)
        result = await service.send_password_reset_email(
            mock_user, "reset-token", ip_address="192.168.1.1",
        )

        assert result is True
        call_args = mock_renderer.render.call_args
        assert call_args[0][0] == "password-reset"
        assert "reset-token" in call_args[0][1]["RESET_URL"]
        assert call_args[0][1]["IP_ADDRESS"] == "192.168.1.1"


async def test_send_welcome_email(
    mock_user: "MockUser", mock_mailer: AsyncMock, mock_settings: MagicMock,
) -> None:
    """Test sending welcome email."""
    with patch("app.domain.web.email.get_settings", return_value=mock_settings):
        mock_renderer = MagicMock()
        mock_renderer.template_exists.return_value = True
        mock_renderer.render.return_value = "<p>Welcome</p>"

        service = EmailMessageService(mailer=mock_mailer, renderer=mock_renderer)
        result = await service.send_welcome_email(mock_user)

        assert result is True
        call_args = mock_renderer.render.call_args
        assert call_args[0][0] == "welcome"


async def test_send_team_invitation_email(mock_mailer: AsyncMock, mock_settings: MagicMock) -> None:
    """Test sending team invitation email."""
    with patch("app.domain.web.email.get_settings", return_value=mock_settings):
        mock_renderer = MagicMock()
        mock_renderer.template_exists.return_value = True
        mock_renderer.render.return_value = "<p>Invitation</p>"

        service = EmailMessageService(mailer=mock_mailer, renderer=mock_renderer)
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


def test_html_to_text_basic(mock_mailer: AsyncMock, mock_settings: MagicMock) -> None:
    """Test HTML to text conversion with basic HTML."""
    with patch("app.domain.web.email.get_settings", return_value=mock_settings):
        service = EmailMessageService(mailer=mock_mailer)
        result = service._html_to_text("<p>Hello <b>World</b></p>")
        assert result == "Hello World"


def test_html_to_text_entities(mock_mailer: AsyncMock, mock_settings: MagicMock) -> None:
    """Test HTML to text conversion with HTML entities."""
    with patch("app.domain.web.email.get_settings", return_value=mock_settings):
        service = EmailMessageService(mailer=mock_mailer)
        result = service._html_to_text("&nbsp;&amp;&lt;&gt;&quot;")
        assert "&" in result
        assert "<" in result
        assert ">" in result


def test_html_to_text_whitespace(mock_mailer: AsyncMock, mock_settings: MagicMock) -> None:
    """Test HTML to text conversion collapses whitespace."""
    with patch("app.domain.web.email.get_settings", return_value=mock_settings):
        service = EmailMessageService(mailer=mock_mailer)
        result = service._html_to_text("<p>  Hello   World  </p>")
        assert result == "Hello World"


def test_app_name_property(mock_mailer: AsyncMock, mock_settings: MagicMock) -> None:
    """Test app_name property returns correct value."""
    with patch("app.domain.web.email.get_settings", return_value=mock_settings):
        service = EmailMessageService(mailer=mock_mailer)
        assert service.app_name == "TestApp"


def test_base_url_property(mock_mailer: AsyncMock, mock_settings: MagicMock) -> None:
    """Test base_url property returns correct value."""
    with patch("app.domain.web.email.get_settings", return_value=mock_settings):
        service = EmailMessageService(mailer=mock_mailer)
        assert service.base_url == "http://test.example.com"


async def test_send_email_exception_with_fail_silently(mock_mailer: AsyncMock, mock_settings: MagicMock) -> None:
    """Test that exceptions are suppressed with fail_silently=True."""
    mock_mailer.send_message.side_effect = Exception("SMTP Error")

    with patch("app.domain.web.email.get_settings", return_value=mock_settings):
        service = EmailMessageService(mailer=mock_mailer, fail_silently=True)
        result = await service.send_email(
            to_email="test@example.com",
            subject="Test",
            html_content="<p>Test</p>",
        )

        assert result is False


async def test_send_email_exception_without_fail_silently(mock_mailer: AsyncMock, mock_settings: MagicMock) -> None:
    """Test that exceptions are raised with fail_silently=False."""
    mock_mailer.send_message.side_effect = Exception("SMTP Error")

    with patch("app.domain.web.email.get_settings", return_value=mock_settings):
        service = EmailMessageService(mailer=mock_mailer, fail_silently=False)
        with pytest.raises(Exception, match="SMTP Error"):
            await service.send_email(
                to_email="test@example.com",
                subject="Test",
                html_content="<p>Test</p>",
            )

"""Tests for email backends."""

from __future__ import annotations

import pytest

from app.lib.email.backends import get_backend, get_backend_class, list_backends, register_backend
from app.lib.email.backends.base import BaseEmailBackend
from app.lib.email.backends.console import ConsoleBackend
from app.lib.email.backends.locmem import InMemoryBackend
from app.lib.email.backends.smtp import AsyncSMTPBackend
from app.lib.email.base import EmailMessage

pytestmark = pytest.mark.anyio


def test_list_backends_contains_builtin() -> None:
    """Test that list_backends returns built-in backends."""
    backends = list_backends()
    assert "smtp" in backends
    assert "console" in backends
    assert "locmem" in backends


def test_get_backend_class_by_short_name() -> None:
    """Test getting backend class by short name."""
    assert get_backend_class("smtp") is AsyncSMTPBackend
    assert get_backend_class("console") is ConsoleBackend
    assert get_backend_class("locmem") is InMemoryBackend


def test_get_backend_class_by_full_path() -> None:
    """Test getting backend class by full Python path."""
    backend_class = get_backend_class("app.lib.email.backends.console.ConsoleBackend")
    assert backend_class is ConsoleBackend


def test_get_backend_class_unknown_raises() -> None:
    """Test that getting unknown backend raises KeyError."""
    with pytest.raises((KeyError, ModuleNotFoundError)):
        get_backend_class("nonexistent")


def test_register_backend_decorator() -> None:
    """Test the register_backend decorator."""

    @register_backend("test_backend")
    class TestBackend(BaseEmailBackend):
        async def send_messages(self, messages: list[EmailMessage]) -> int:
            return len(messages)

    backends = list_backends()
    assert "test_backend" in backends
    assert get_backend_class("test_backend") is TestBackend


def test_get_backend_returns_instance(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_backend returns configured backend instance."""
    monkeypatch.setenv("EMAIL_BACKEND", "console")
    backend = get_backend()
    assert isinstance(backend, ConsoleBackend)


def test_get_backend_with_fail_silently(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_backend respects fail_silently parameter."""
    monkeypatch.setenv("EMAIL_BACKEND", "console")
    backend = get_backend(fail_silently=True)
    assert backend.fail_silently is True


@pytest.mark.usefixtures("clear_email_outbox")
async def test_inmemory_backend_stores_messages() -> None:
    """Test InMemoryBackend stores messages in outbox."""
    backend = InMemoryBackend()
    message = EmailMessage(
        subject="Test",
        body="Test body",
        to=["test@example.com"],
    )

    num_sent = await backend.send_messages([message])

    assert num_sent == 1
    assert len(InMemoryBackend.outbox) == 1
    assert InMemoryBackend.outbox[0].subject == "Test"


@pytest.mark.usefixtures("clear_email_outbox")
async def test_inmemory_backend_clear() -> None:
    """Test InMemoryBackend clear method."""
    backend = InMemoryBackend()
    message = EmailMessage(subject="Test", body="Body", to=["test@example.com"])

    await backend.send_messages([message])
    assert len(InMemoryBackend.outbox) == 1

    InMemoryBackend.clear()
    assert len(InMemoryBackend.outbox) == 0


async def test_console_backend_sends_messages(capsys: pytest.CaptureFixture[str]) -> None:
    """Test ConsoleBackend prints to stdout."""
    backend = ConsoleBackend()
    message = EmailMessage(
        subject="Console Test",
        body="Console body",
        to=["console@example.com"],
    )

    num_sent = await backend.send_messages([message])

    assert num_sent == 1
    captured = capsys.readouterr()
    assert "Console Test" in captured.out
    assert "console@example.com" in captured.out


async def test_backend_context_manager() -> None:
    """Test backend async context manager protocol."""
    backend = InMemoryBackend()

    async with backend as ctx_backend:
        assert ctx_backend is backend


def test_base_backend_fail_silently_default() -> None:
    """Test BaseEmailBackend has fail_silently=False by default."""
    backend = InMemoryBackend()
    assert backend.fail_silently is False


def test_base_backend_fail_silently_configurable() -> None:
    """Test BaseEmailBackend fail_silently is configurable."""
    backend = InMemoryBackend(fail_silently=True)
    assert backend.fail_silently is True

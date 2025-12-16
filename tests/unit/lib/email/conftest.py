"""Pytest fixtures for email tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import pytest

from app.lib.email.backends.locmem import InMemoryBackend
from app.lib.email.base import EmailMessage, EmailMultiAlternatives

if TYPE_CHECKING:
    from collections.abc import Generator


@dataclass
class MockUser:
    """Mock user for testing email service."""

    email: str
    name: str | None = None


@pytest.fixture
def mock_user() -> MockUser:
    """Create a mock user for testing."""
    return MockUser(email="test@example.com", name="Test User")


@pytest.fixture
def sample_email_message() -> EmailMessage:
    """Create a sample email message for testing."""
    return EmailMessage(
        subject="Test Subject",
        body="Test body content",
        from_email="sender@example.com",
        to=["recipient@example.com"],
    )


@pytest.fixture
def sample_html_email() -> EmailMultiAlternatives:
    """Create a sample HTML email message for testing."""
    return EmailMultiAlternatives(
        subject="HTML Test",
        body="Plain text version",
        html_body="<h1>HTML version</h1>",
        from_email="sender@example.com",
        to=["recipient@example.com"],
    )


@pytest.fixture
def clear_email_outbox() -> Generator[None, None, None]:
    """Clear the in-memory email outbox before and after tests."""
    InMemoryBackend.clear()
    yield
    InMemoryBackend.clear()

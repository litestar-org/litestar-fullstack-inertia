"""Pytest fixtures for email tests."""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import AsyncMock

import pytest
from litestar_email import EmailMessage, EmailMultiAlternatives


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
def mock_mailer() -> AsyncMock:
    """Create a mock mailer (litestar-email EmailService) for testing."""
    mailer = AsyncMock()
    mailer.send_message = AsyncMock(return_value=None)
    return mailer

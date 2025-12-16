"""Tests for email base classes."""

from __future__ import annotations

from app.lib.email.base import EmailMessage, EmailMultiAlternatives


def test_email_message_defaults() -> None:
    """Test EmailMessage has correct defaults."""
    msg = EmailMessage(subject="Test", body="Body")

    assert msg.subject == "Test"
    assert msg.body == "Body"
    assert msg.from_email is None
    assert msg.to == []
    assert msg.cc == []
    assert msg.bcc == []
    assert msg.reply_to == []
    assert msg.headers == {}
    assert msg.attachments == []
    assert msg.alternatives == []


def test_email_message_with_all_fields() -> None:
    """Test EmailMessage with all fields populated."""
    msg = EmailMessage(
        subject="Full Test",
        body="Full body",
        from_email="sender@example.com",
        to=["recipient@example.com"],
        cc=["cc@example.com"],
        bcc=["bcc@example.com"],
        reply_to=["reply@example.com"],
        headers={"X-Custom": "Value"},
        attachments=[("file.txt", b"content", "text/plain")],
        alternatives=[("<p>HTML</p>", "text/html")],
    )

    assert msg.subject == "Full Test"
    assert msg.from_email == "sender@example.com"
    assert msg.to == ["recipient@example.com"]
    assert msg.cc == ["cc@example.com"]
    assert msg.bcc == ["bcc@example.com"]
    assert msg.reply_to == ["reply@example.com"]
    assert msg.headers == {"X-Custom": "Value"}
    assert len(msg.attachments) == 1
    assert len(msg.alternatives) == 1


def test_email_multi_alternatives_adds_html() -> None:
    """Test EmailMultiAlternatives adds HTML to alternatives."""
    msg = EmailMultiAlternatives(
        subject="HTML Email",
        body="Plain text",
        html_body="<p>HTML content</p>",
        to=["test@example.com"],
    )

    assert msg.body == "Plain text"
    assert len(msg.alternatives) == 1
    assert msg.alternatives[0] == ("<p>HTML content</p>", "text/html")


def test_email_multi_alternatives_without_html() -> None:
    """Test EmailMultiAlternatives without HTML."""
    msg = EmailMultiAlternatives(
        subject="Plain Email",
        body="Plain text only",
        to=["test@example.com"],
    )

    assert msg.body == "Plain text only"
    assert msg.alternatives == []


def test_email_multi_alternatives_preserves_existing_alternatives() -> None:
    """Test EmailMultiAlternatives preserves existing alternatives."""
    msg = EmailMultiAlternatives(
        subject="Multi",
        body="Plain",
        html_body="<p>HTML</p>",
        to=["test@example.com"],
        alternatives=[("existing", "text/custom")],
    )

    assert len(msg.alternatives) == 2
    assert ("existing", "text/custom") in msg.alternatives
    assert ("<p>HTML</p>", "text/html") in msg.alternatives


def test_email_message_attachments_structure() -> None:
    """Test attachment tuple structure (filename, content, mimetype)."""
    msg = EmailMessage(
        subject="With Attachment",
        body="Body",
        attachments=[
            ("document.pdf", b"%PDF-content", "application/pdf"),
            ("image.png", b"\x89PNG", "image/png"),
        ],
    )

    assert len(msg.attachments) == 2
    filename, content, mimetype = msg.attachments[0]
    assert filename == "document.pdf"
    assert content == b"%PDF-content"
    assert mimetype == "application/pdf"


def test_email_message_immutable_defaults() -> None:
    """Test that default lists are independent between instances."""
    msg1 = EmailMessage(subject="One", body="Body")
    msg2 = EmailMessage(subject="Two", body="Body")

    msg1.to.append("one@example.com")

    assert msg1.to == ["one@example.com"]
    assert msg2.to == []

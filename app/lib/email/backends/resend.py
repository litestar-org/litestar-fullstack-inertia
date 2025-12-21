"""Resend email backend using the Resend HTTP API."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import httpx

from app.lib.email.backends import register_backend
from app.lib.email.backends.base import BaseEmailBackend

if TYPE_CHECKING:
    from app.lib.email.base import EmailMessage

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"


@register_backend("resend")
class ResendBackend(BaseEmailBackend):
    """Resend email backend using the HTTP API.

    This backend sends emails via Resend's HTTP API, which doesn't require
    SMTP ports and works on any hosting plan.

    Example:
        EMAIL_BACKEND=resend
        RESEND_API_KEY=re_xxxxxxxxxxxx
        EMAIL_FROM=noreply@yourdomain.com

    Get your API key at: https://resend.com/api-keys
    """

    def __init__(
        self,
        fail_silently: bool = False,
        api_key: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize Resend backend.

        Args:
            fail_silently: If True, suppress exceptions during send.
            api_key: Resend API key. If None, uses settings.
            **kwargs: Additional arguments (ignored).
        """
        super().__init__(fail_silently=fail_silently, **kwargs)

        from app.lib.settings import get_settings

        settings = get_settings().email
        self.api_key = api_key if api_key is not None else settings.RESEND_API_KEY
        self._client: httpx.AsyncClient | None = None

    async def open(self) -> bool:
        """Open an HTTP client for sending emails.

        Returns:
            True if a new client was created, False if reusing existing.
        """
        if self._client is not None:
            return False

        self._client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )
        return True

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            try:
                await self._client.aclose()
            except Exception:
                logger.exception("Error closing Resend HTTP client")
                if not self.fail_silently:
                    raise
            finally:
                self._client = None

    async def send_messages(self, messages: list[EmailMessage]) -> int:
        """Send messages via Resend API.

        Args:
            messages: List of EmailMessage instances to send.

        Returns:
            Number of messages successfully sent.
        """
        if not messages:
            return 0

        new_connection = await self.open()

        try:
            num_sent = 0
            for message in messages:
                try:
                    await self._send_message(message)
                    num_sent += 1
                except Exception:
                    logger.exception("Failed to send email to %s via Resend", message.to)
                    if not self.fail_silently:
                        raise
            return num_sent
        finally:
            if new_connection:
                await self.close()

    async def _send_message(self, message: EmailMessage) -> None:
        """Send a single message via Resend API.

        Args:
            message: The email message to send.
        """
        if self._client is None:
            err_msg = "Resend client not initialized"
            raise RuntimeError(err_msg)

        from app.lib.settings import get_settings

        settings = get_settings().email

        # Build the request payload
        payload: dict[str, Any] = {
            "from": message.from_email or settings.FROM_EMAIL,
            "to": message.to,
            "subject": message.subject,
        }

        # Add text body
        if message.body:
            payload["text"] = message.body

        # Add HTML alternative if present
        for content, mimetype in message.alternatives:
            if mimetype == "text/html":
                payload["html"] = content
                break

        # Add optional fields
        if message.cc:
            payload["cc"] = message.cc
        if message.bcc:
            payload["bcc"] = message.bcc
        if message.reply_to:
            payload["reply_to"] = message.reply_to[0] if len(message.reply_to) == 1 else message.reply_to

        # Add custom headers
        if message.headers:
            payload["headers"] = message.headers

        # Note: Attachments would require base64 encoding
        # For now, log a warning if attachments are present
        if message.attachments:
            logger.warning("Resend backend: attachments not yet implemented, skipping %d attachments", len(message.attachments))

        response = await self._client.post(RESEND_API_URL, json=payload)

        if response.status_code >= 400:
            error_detail = response.text
            logger.error("Resend API error (%d): %s", response.status_code, error_detail)
            msg = f"Resend API error: {response.status_code} - {error_detail}"
            raise RuntimeError(msg)

        logger.info("Email sent to %s via Resend with subject: %s", message.to, message.subject)

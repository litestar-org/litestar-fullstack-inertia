"""Proxy headers middleware for reverse proxy support.

This module provides middleware to handle X-Forwarded-* headers from reverse proxies
like Railway, Heroku, AWS ALB, etc.

Temporary workaround for: https://github.com/litestar-org/litestar-vite/issues/167
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from litestar.middleware.base import MiddlewareProtocol

if TYPE_CHECKING:
    from litestar.types import ASGIApp, Receive, Scope, Send


class ProxyHeadersMiddleware(MiddlewareProtocol):
    """Middleware to respect X-Forwarded-Proto header from reverse proxies.

    When deployed behind a reverse proxy that terminates SSL (Railway, Heroku, AWS ALB),
    the incoming request appears as HTTP. This middleware updates the ASGI scope's scheme
    based on the X-Forwarded-Proto header so that url_for() and base_url generate correct
    HTTPS URLs.
    """

    def __init__(self, app: ASGIApp) -> None:
        """Initialize the middleware.

        Args:
            app: The ASGI application.
        """
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Process the request and update scheme from X-Forwarded-Proto.

        Args:
            scope: The ASGI scope.
            receive: The receive callable.
            send: The send callable.
        """
        if scope["type"] == "http":
            headers = dict(scope.get("headers", []))
            forwarded_proto = headers.get(b"x-forwarded-proto", b"").decode()
            if forwarded_proto in ("https", "http"):
                scope["scheme"] = forwarded_proto

        await self.app(scope, receive, send)

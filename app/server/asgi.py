from __future__ import annotations

from litestar import Litestar

from app.server import plugins


def create_app() -> Litestar:
    """Create ASGI application.

    Returns:
        The ASGI application.
    """
    return Litestar(plugins=[plugins.app_core])

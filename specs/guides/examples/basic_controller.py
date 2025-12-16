from __future__ import annotations

from typing import TYPE_CHECKING

from litestar import Controller, get, post
from litestar_vite.inertia import InertiaRedirect

if TYPE_CHECKING:
    from litestar import Request



class ExampleController(Controller):
    """Example Controller demonstrating patterns."""

    path = "/examples"
    tags = ["Examples"]

    @get(component="examples/list", path="/", name="examples.list")
    async def list_items(self) -> dict:
        """Inertia page - returns props as dict."""
        return {"message": "Hello from Litestar!"}

    @post(path="/", name="examples.create")
    async def create_item(
        self,
        request: Request,
    ) -> InertiaRedirect:
        """Handle form submission - redirect on success."""
        # Logic here...
        return InertiaRedirect(request, request.url_for("examples.list"))

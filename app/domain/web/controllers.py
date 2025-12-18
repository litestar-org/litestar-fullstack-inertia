from litestar import Controller, Request, get
from litestar.response import File
from litestar_vite.inertia import InertiaRedirect

from app.lib.schema import NoProps
from app.lib.settings import BASE_DIR


class WebController(Controller):
    """Web Controller."""

    include_in_schema = False

    @get(path="/", name="home", exclude_from_auth=True)
    async def home(self, request: Request) -> InertiaRedirect:
        """Serve site root.

        Returns:
            Redirect to dashboard if authenticated, otherwise redirect to landing.
        """
        if request.session.get("user_id", False):
            return InertiaRedirect(request, request.url_for("dashboard"))
        return InertiaRedirect(request, request.url_for("landing"))

    @get(component="landing", path="/landing/", name="landing", exclude_from_auth=True)
    async def landing(self) -> NoProps:
        """Serve landing page.

        Returns:
            Empty page props.
        """
        return NoProps()

    @get(component="dashboard", path="/dashboard/", name="dashboard")
    async def dashboard(self) -> NoProps:
        """Serve dashboard page.

        Returns:
            Empty page props.
        """
        return NoProps()

    @get(component="about", path="/about/", name="about")
    async def about(self) -> NoProps:
        """Serve about page.

        Returns:
            Empty page props.
        """
        return NoProps()

    @get(component="legal/privacy-policy", path="/privacy-policy/", name="privacy-policy", exclude_from_auth=True)
    async def privacy_policy(self) -> NoProps:
        """Serve privacy policy page.

        Returns:
            Empty page props.
        """
        return NoProps()

    @get(component="legal/terms-of-service", path="/terms-of-service/", name="terms-of-service", exclude_from_auth=True)
    async def terms_of_service(self) -> NoProps:
        """Serve terms of service page.

        Returns:
            Empty page props.
        """
        return NoProps()

    @get(path="/favicon.ico", name="favicon", exclude_from_auth=True, include_in_schema=False, sync_to_thread=False)
    def favicon(self) -> File:
        """Serve favicon.

        Returns:
            Favicon file response.
        """
        return File(path=BASE_DIR / "domain" / "web" / "public" / "favicon.ico")

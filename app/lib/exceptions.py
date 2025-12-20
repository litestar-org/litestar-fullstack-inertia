from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import quote, urlparse, urlunparse

from litestar.exceptions import HTTPException, NotAuthorizedException
from litestar.response import Response
from litestar.status_codes import HTTP_401_UNAUTHORIZED
from litestar_vite.inertia import flash
from litestar_vite.inertia.exception_handler import create_inertia_exception_response as _original_handler
from litestar_vite.inertia.plugin import InertiaPlugin
from litestar_vite.inertia.response import InertiaRedirect

if TYPE_CHECKING:
    from litestar.connection import Request
    from litestar.connection.base import AuthT, StateT, UserT


__all__ = (
    "ApplicationClientError",
    "ApplicationError",
    "AuthorizationError",
    "HealthCheckConfigurationError",
    "MissingDependencyError",
    "inertia_exception_handler",
)


# TODO: Remove this workaround after litestar-vite > 0.15.0rc3 is released.
# This fixes the issue where flash messages don't work for unauthorized redirects
# because no session exists yet. The fix passes the error via query parameter instead.
# See: https://github.com/litestar-org/litestar-vite/issues/164
def inertia_exception_handler(request: "Request[UserT, AuthT, StateT]", exc: "Exception") -> "Response[Any]":
    """Workaround exception handler that passes error via query param when flash fails.

    This is a temporary fix until litestar-vite > 0.15.0rc3 is released with the proper fix.
    """
    # Check if this is an unauthorized error that would redirect to login
    status_code = exc.status_code if isinstance(exc, HTTPException) else 500
    is_unauthorized = status_code == HTTP_401_UNAUTHORIZED or isinstance(exc, NotAuthorizedException)

    if not is_unauthorized:
        return _original_handler(request, exc)

    # Try to get the inertia plugin config
    inertia_plugin: InertiaPlugin | None
    try:
        inertia_plugin = request.app.plugins.get("InertiaPlugin")
    except KeyError:
        inertia_plugin = None

    if inertia_plugin is None:
        return _original_handler(request, exc)

    redirect_to_login = inertia_plugin.config.redirect_unauthorized_to
    if redirect_to_login is None or request.url.path == redirect_to_login:
        return _original_handler(request, exc)

    # Try to flash, check if it succeeded
    detail = exc.detail if isinstance(exc, HTTPException) else str(exc)
    flash_succeeded = False
    if detail:
        flash_succeeded = flash(request, detail, category="error")

    # If flash failed, add error to query params
    if not flash_succeeded and detail:
        parsed = urlparse(redirect_to_login)
        error_param = f"error={quote(detail, safe='')}"
        query = f"{parsed.query}&{error_param}" if parsed.query else error_param
        redirect_to_login = urlunparse(parsed._replace(query=query))

    return InertiaRedirect(request, redirect_to=redirect_to_login)


class ApplicationError(Exception):
    """Base exception type for the lib's custom exception types."""

    detail: str

    def __init__(self, *args: Any, detail: str = "") -> None:
        """Initialize ``AdvancedAlchemyException``.

        Args:
            *args: args are converted to :class:`str` before passing to :class:`Exception`
            detail: detail of the exception.
        """
        str_args = [str(arg) for arg in args if arg]
        if not detail:
            if str_args:
                detail, *str_args = str_args
            elif hasattr(self, "detail"):
                detail = self.detail
        self.detail = detail
        super().__init__(*str_args)

    def __repr__(self) -> str:
        if self.detail:
            return f"{self.__class__.__name__} - {self.detail}"
        return self.__class__.__name__

    def __str__(self) -> str:
        return " ".join((*self.args, self.detail)).strip()


class MissingDependencyError(ApplicationError, ImportError):
    """Missing optional dependency.

    This exception is raised only when a module depends on a dependency that has not been installed.
    """


class ApplicationClientError(ApplicationError):
    """Base exception type for client errors."""


class AuthorizationError(ApplicationClientError):
    """A user tried to do something they shouldn't have."""


class HealthCheckConfigurationError(ApplicationError):
    """An error occurred while registering an health check."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from advanced_alchemy.exceptions import IntegrityError, NotFoundError, RepositoryError
from litestar.exceptions import HTTPException
from litestar.response import Response
from litestar.status_codes import HTTP_404_NOT_FOUND
from litestar_vite.inertia import flash
from litestar_vite.inertia.exception_handler import create_inertia_exception_response as inertia_exception_handler
from litestar_vite.inertia.response import InertiaBack

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
    "integrity_error_handler",
    "not_found_error_handler",
    "repository_error_handler",
)


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


def integrity_error_handler(request: "Request[UserT, AuthT, StateT]", exc: IntegrityError) -> "Response[Any]":
    """Handle database integrity errors (constraint violations) as validation errors.

    Returns:
        an Inertia-compatible error response with a flash message and redirect back.
    """
    detail = exc.detail if hasattr(exc, "detail") and exc.detail else str(exc)
    flash(request, detail, category="error")
    return InertiaBack(request)


def not_found_error_handler(request: "Request[UserT, AuthT, StateT]", exc: NotFoundError) -> "Response[Any]":
    """Handle repository not found errors as 404 responses.

    Returns:
        an Inertia-compatible 404 error response.
    """
    detail = exc.detail if hasattr(exc, "detail") and exc.detail else "Resource not found"
    # Use the Inertia exception handler which knows how to create proper error pages
    http_exc = HTTPException(status_code=HTTP_404_NOT_FOUND, detail=detail)
    return inertia_exception_handler(request, http_exc)


def repository_error_handler(request: "Request[UserT, AuthT, StateT]", exc: RepositoryError) -> "Response[Any]":
    """Handle general repository errors as validation errors.

    Returns:
        an Inertia-compatible error response with a flash message and redirect back.
    """
    detail = exc.detail if hasattr(exc, "detail") and exc.detail else "An error occurred processing your request"
    flash(request, detail, category="error")
    return InertiaBack(request)

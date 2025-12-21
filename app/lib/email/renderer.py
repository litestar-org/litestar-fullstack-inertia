"""Email template renderer using pre-built HTML templates.

This module provides a template renderer that uses simple placeholder
substitution instead of Jinja2, loading pre-built HTML templates from
the templates directory.

The template system uses {{PLACEHOLDER}} syntax with automatic HTML escaping.
"""

from __future__ import annotations

import html
import re
from functools import lru_cache
from pathlib import Path  # noqa: TC003 - used at module level for DEFAULT_TEMPLATE_DIR
from typing import Any

from app.lib.settings import BASE_DIR

# Default template directory for email templates
DEFAULT_TEMPLATE_DIR = BASE_DIR / "lib" / "email" / "templates"

# Pattern for placeholder matching: {{VARIABLE_NAME}}
PLACEHOLDER_PATTERN = re.compile(r"\{\{(\w+)\}\}")


class TemplateRenderer:
    """Renders pre-built email templates with data injection.

    Uses simple placeholder replacement instead of Jinja2.
    Placeholders use {{VARIABLE_NAME}} syntax.

    The renderer caches loaded templates for performance.

    Example:
        renderer = TemplateRenderer()
        html = renderer.render("password-reset", {
            "USER_NAME": "John",
            "RESET_URL": "https://example.com/reset?token=abc",
            "EXPIRES_MINUTES": 60,
        })
    """

    def __init__(self, template_dir: Path | None = None) -> None:
        """Initialize the template renderer.

        Args:
            template_dir: Directory containing template files.
                         Defaults to lib/email/templates.
        """
        self.template_dir = template_dir or DEFAULT_TEMPLATE_DIR
        self._cache: dict[str, str] = {}

    def render(self, template_name: str, context: dict[str, Any]) -> str:
        """Render a template with the given context.

        Placeholders in the template are replaced with values from the
        context dictionary. Values are HTML-escaped for security.

        Args:
            template_name: Name of template file (without extension).
            context: Dictionary of values to inject into placeholders.

        Returns:
            Rendered HTML string.

        Raises:
            FileNotFoundError: If template file does not exist.

        Example:
            html = renderer.render("welcome", {
                "USER_NAME": "Alice",
                "APP_NAME": "MyApp",
            })
        """
        template = self._load_template(template_name)

        def replace_placeholder(match: re.Match[str]) -> str:
            key = match.group(1)
            value = context.get(key)
            if value is None:
                # Return a visible marker for missing placeholders in debug
                return f"{{{{MISSING:{key}}}}}"
            return self._escape_html(str(value))

        return PLACEHOLDER_PATTERN.sub(replace_placeholder, template)

    def render_unsafe(self, template_name: str, context: dict[str, Any]) -> str:
        """Render a template without HTML escaping.

        Use this only when context values are already safe HTML.

        Args:
            template_name: Name of template file (without extension).
            context: Dictionary of values to inject into placeholders.

        Returns:
            Rendered HTML string (values not escaped).
        """
        template = self._load_template(template_name)

        def replace_placeholder(match: re.Match[str]) -> str:
            key = match.group(1)
            value = context.get(key)
            if value is None:
                return f"{{{{MISSING:{key}}}}}"
            return str(value)

        return PLACEHOLDER_PATTERN.sub(replace_placeholder, template)

    def _load_template(self, template_name: str) -> str:
        """Load template from file or cache.

        Args:
            template_name: Name of template file (without extension).

        Returns:
            Template content as string.

        Raises:
            FileNotFoundError: If template file does not exist.
        """
        if template_name not in self._cache:
            template_path = self.template_dir / f"{template_name}.html"
            if not template_path.exists():
                msg = f"Email template not found: {template_path}"
                raise FileNotFoundError(msg)
            self._cache[template_name] = template_path.read_text(encoding="utf-8")
        return self._cache[template_name]

    def template_exists(self, template_name: str) -> bool:
        """Check if a template exists.

        Args:
            template_name: Name of template file (without extension).

        Returns:
            True if template exists, False otherwise.
        """
        template_path = self.template_dir / f"{template_name}.html"
        return template_path.exists()

    @staticmethod
    def _escape_html(text: str) -> str:
        """Escape HTML special characters.

        Args:
            text: Text to escape.

        Returns:
            HTML-escaped text.
        """
        return html.escape(text, quote=True)

    def clear_cache(self) -> None:
        """Clear template cache.

        Useful for development when templates are being edited.
        """
        self._cache.clear()


@lru_cache(maxsize=1)
def get_template_renderer() -> TemplateRenderer:
    """Get the global template renderer instance.

    Returns:
        Cached TemplateRenderer instance.
    """
    return TemplateRenderer()

"""Tests for email template renderer."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

import pytest

from app.lib.email.renderer import TemplateRenderer, get_template_renderer

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture
def temp_template_dir() -> Generator[Path, None, None]:
    """Create a temporary directory with test templates."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create a test template
        (tmppath / "test-template.html").write_text(
            "<h1>Hello {{USER_NAME}}</h1><p>Your code is {{CODE}}</p>",
        )

        # Create template with special characters
        (tmppath / "special-chars.html").write_text(
            "<p>{{CONTENT}}</p>",
        )

        yield tmppath


def test_render_template_basic(temp_template_dir: Path) -> None:
    """Test basic template rendering with placeholder substitution."""
    renderer = TemplateRenderer(template_dir=temp_template_dir)

    result = renderer.render("test-template", {
        "USER_NAME": "Alice",
        "CODE": "12345",
    })

    assert "<h1>Hello Alice</h1>" in result
    assert "Your code is 12345" in result


def test_render_escapes_html(temp_template_dir: Path) -> None:
    """Test that template rendering escapes HTML special characters."""
    renderer = TemplateRenderer(template_dir=temp_template_dir)

    result = renderer.render("special-chars", {
        "CONTENT": "<script>alert('xss')</script>",
    })

    assert "&lt;script&gt;" in result
    assert "<script>" not in result


def test_render_unsafe_does_not_escape(temp_template_dir: Path) -> None:
    """Test render_unsafe does not escape HTML."""
    renderer = TemplateRenderer(template_dir=temp_template_dir)

    result = renderer.render_unsafe("special-chars", {
        "CONTENT": "<strong>Bold</strong>",
    })

    assert "<strong>Bold</strong>" in result


def test_render_missing_placeholder_marker(temp_template_dir: Path) -> None:
    """Test that missing placeholders are marked in output."""
    renderer = TemplateRenderer(template_dir=temp_template_dir)

    result = renderer.render("test-template", {
        "USER_NAME": "Bob",
        # CODE is missing
    })

    assert "Hello Bob" in result
    assert "{{MISSING:CODE}}" in result


def test_render_nonexistent_template_raises(temp_template_dir: Path) -> None:
    """Test that rendering nonexistent template raises FileNotFoundError."""
    renderer = TemplateRenderer(template_dir=temp_template_dir)

    with pytest.raises(FileNotFoundError):
        renderer.render("nonexistent", {})


def test_template_exists_true(temp_template_dir: Path) -> None:
    """Test template_exists returns True for existing template."""
    renderer = TemplateRenderer(template_dir=temp_template_dir)
    assert renderer.template_exists("test-template") is True


def test_template_exists_false(temp_template_dir: Path) -> None:
    """Test template_exists returns False for nonexistent template."""
    renderer = TemplateRenderer(template_dir=temp_template_dir)
    assert renderer.template_exists("nonexistent") is False


def test_template_caching(temp_template_dir: Path) -> None:
    """Test that templates are cached after first load."""
    renderer = TemplateRenderer(template_dir=temp_template_dir)

    # First render loads template
    renderer.render("test-template", {"USER_NAME": "First", "CODE": "111"})
    assert "test-template" in renderer._cache

    # Modify the file
    (temp_template_dir / "test-template.html").write_text("<p>Modified</p>")

    # Second render uses cache
    result = renderer.render("test-template", {"USER_NAME": "Second", "CODE": "222"})
    assert "Hello" in result  # Original content, not "Modified"


def test_clear_cache(temp_template_dir: Path) -> None:
    """Test that clear_cache removes cached templates."""
    renderer = TemplateRenderer(template_dir=temp_template_dir)

    # Load template
    renderer.render("test-template", {"USER_NAME": "Test", "CODE": "000"})
    assert "test-template" in renderer._cache

    # Clear cache
    renderer.clear_cache()
    assert len(renderer._cache) == 0


def test_get_template_renderer_returns_cached_instance() -> None:
    """Test get_template_renderer returns the same instance."""
    renderer1 = get_template_renderer()
    renderer2 = get_template_renderer()
    assert renderer1 is renderer2


def test_render_with_numeric_values(temp_template_dir: Path) -> None:
    """Test rendering with non-string values."""
    renderer = TemplateRenderer(template_dir=temp_template_dir)

    result = renderer.render("test-template", {
        "USER_NAME": "Numbers",
        "CODE": 42,
    })

    assert "42" in result


def test_escape_html_static_method() -> None:
    """Test the _escape_html static method."""
    assert TemplateRenderer._escape_html("<>&\"'") == "&lt;&gt;&amp;&quot;&#x27;"

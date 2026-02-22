"""Sphinx configuration."""

from __future__ import annotations

import importlib.metadata
import warnings

from sqlalchemy.exc import SAWarning

warnings.filterwarnings("ignore", category=SAWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)  # RemovedInSphinx80Warning

# -- Project information -----------------------------------------------------
project = importlib.metadata.metadata("app")["Name"]
copyright = "2023, Litestar Organization"
author = "Cody Fincher"
release = importlib.metadata.version("app")

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx_click",
    "sphinx_design",
    "sphinx.ext.todo",
    "sphinx_copybutton",
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinxcontrib.mermaid",
    "sphinx.ext.intersphinx",
    "sphinx.ext.autosectionlabel",
]

exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    # Legacy autodoc trees reference removed modules and currently fail strict docs builds.
    "api/domain/**",
    "api/lib/**",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "anyio": ("https://anyio.readthedocs.io/en/stable/", None),
    "click": ("https://click.palletsprojects.com/en/stable/", None),
    "structlog": ("https://www.structlog.org/en/stable/", None),
    "litestar": ("https://docs.litestar.dev/latest/", None),
    "msgspec": ("https://jcristharif.com/msgspec/", None),
}

napoleon_google_docstring = True
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = False
napoleon_attr_annotations = True

autoclass_content = "both"
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "exclude-members": "__weakref__",
    "show-inheritance": True,
    "class-signature": "separated",
    "typehints-format": "short",
}

autosectionlabel_prefix_document = True
suppress_warnings = [
    "autosectionlabel.*",
    "ref.python",  # TODO: remove when https://github.com/sphinx-doc/sphinx/issues/4961 is fixed
]
todo_include_todos = True

# -- Style configuration -----------------------------------------------------
html_theme = "shibuya"
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_show_sourcelink = True
html_title = "Litestar Fullstack Docs"
html_context = {
    "source_type": "github",
    "source_user": "litestar-org",
    "source_repo": "litestar-fullstack-inertia",
    "source_version": "main",
    "source_docs_path": "docs/",
}
html_theme_options = {
    "accent_color": "blue",
    "github_url": "https://github.com/litestar-org/litestar-fullstack-inertia",
    "logo_target": "https://docs.fullstack.litestar.dev",
    "nav_links": [
        {"title": "Documentation", "url": "index"},
        {
            "title": "Community",
            "children": [
                {
                    "title": "Contributing",
                    "url": "contribution-guide",
                    "summary": "Learn how to contribute to Litestar Fullstack",
                },
                {
                    "title": "Code of Conduct",
                    "url": "https://github.com/litestar-org/.github/blob/main/CODE_OF_CONDUCT.md",
                    "external": True,
                    "summary": "Review the etiquette for interacting with the Litestar community",
                },
            ],
        },
        {
            "title": "About",
            "children": [
                {
                    "title": "Litestar Organization",
                    "url": "https://litestar.dev/about/organization.html",
                    "external": True,
                    "summary": "About the Litestar organization",
                },
            ],
        },
    ],
}

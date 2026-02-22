# SPDX-FileCopyrightText: 2023-present Cody Fincher <cody.fincher@gmail.com>
#
# SPDX-License-Identifier: MIT
from __future__ import annotations

import os
import sys
from pathlib import Path

run_litestar_cli = None
_run_litestar_cli_import_error: ImportError | None = None

try:
    from litestar.__main__ import run_cli as run_litestar_cli

    _run_litestar_cli_import_error = None
except ImportError as exc:
    run_litestar_cli = None
    _run_litestar_cli_import_error = exc


def run_cli() -> None:
    """Application Entrypoint."""
    current_path = Path(__file__).parent.parent.resolve()
    sys.path.append(str(current_path))
    os.environ.setdefault("LITESTAR_APP", "app.server.asgi:create_app")
    os.environ.setdefault("LITESTAR_APP_NAME", "Litestar Inertia Reference App")
    os.environ.setdefault("LITESTAR_GRANIAN_IN_SUBPROCESS", "false")
    os.environ.setdefault("LITESTAR_GRANIAN_USE_LITESTAR_LOGGER", "true")
    if run_litestar_cli is None:
        print(  # noqa: T201
            "Could not load required libraries.  ",
            "Please check your installation and make sure you activated any necessary virtual environment",
        )
        if _run_litestar_cli_import_error is not None:
            print(_run_litestar_cli_import_error)  # noqa: T201
        sys.exit(1)
    run_litestar_cli()


if __name__ == "__main__":
    run_cli()

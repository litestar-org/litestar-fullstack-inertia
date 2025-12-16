===========
Development
===========

This section describes the development workflow, tools, and standards for the project.

Makefile & Tools
----------------

We use ``make`` to orchestrate development tasks, wrapping modern tools like ``uv`` (Python) and ``bun`` (JavaScript).

Common Commands
^^^^^^^^^^^^^^^

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Command
     - Description
   * - ``make install``
     - Fresh install of all dependencies (Python + JS) and environment setup.
   * - ``make start-infra``
     - Start Dockerized services (PostgreSQL, Redis).
   * - ``make run``
     - Start the full stack (Backend + Vite) in development mode.
   * - ``make test``
     - Run the full test suite with ``pytest``.
   * - ``make lint``
     - Run all linters (Ruff, Mypy, Biome, Slotscheck).
   * - ``make upgrade``
     - Upgrade all dependencies and pre-commit hooks.

Code Style & Quality
--------------------

We enforce strict quality gates using pre-commit hooks.

Python Standards
^^^^^^^^^^^^^^^^
- **Linter/Formatter**: `Ruff <https://docs.astral.sh/ruff/>`_
- **Type Checking**: `Mypy <https://mypy-lang.org/>`_ and `Pyright <https://github.com/microsoft/pyright>`_
- **Style**: Google-style docstrings, strict type hints (PEP 604 `T | None`), no `from __future__ import annotations`.

Frontend Standards
^^^^^^^^^^^^^^^^^^
- **Linter/Formatter**: `Biome <https://biomejs.dev/>`_
- **Style**: strict TypeScript, functional React components.

Testing Strategy
----------------

We use **pytest** with **anyio** for async support.

- **Unit Tests**: Isolated logic tests.
- **Integration Tests**: Full API and Database integration tests using `pytest-databases`.
- **Frontend Tests**: Component testing via Vitest (configured in ``vite.config.ts``).

.. code-block:: shell

    # Run tests with coverage
    make coverage

Full Makefile
-------------

.. dropdown:: Full Makefile

    .. literalinclude:: ../../Makefile
        :language: make

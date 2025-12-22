# Testing Guide

**Project**: Litestar Fullstack Inertia
**Status**: Active

## Overview

We use **pytest** as our primary testing framework, configured with **anyio** for async support and **pytest-databases** for Docker-based database fixtures.

## Tools & Configuration

- **Runner**: `pytest`
- **Async Backend**: `anyio` (forced to `asyncio` in `tests/conftest.py`)
- **Coverage**: `pytest-cov` (target: 90%+)
- **Database**: `pytest-databases[postgres]` (manages test DB containers)

## Test Structure

```
tests/
├── conftest.py          # Global fixtures (AnyIO backend, settings patching)
├── data_fixtures.py     # Shared data fixtures (users, teams, etc.)
├── helpers.py           # Helper functions for tests
├── unit/                # Unit tests (isolated logic)
└── integration/         # Integration tests (DB, API, full flow)
```

## Key Fixtures

Defined in `tests/conftest.py`:

- `anyio_backend`: Forces `asyncio` scope.
- `_patch_settings`: Overrides `app.lib.settings` with `.env.testing` values and disables Vite dev mode.

## Running Tests

We use `make` commands to run tests (see `Makefile`):

```bash
# Run all tests
make test

# Run all tests with coverage
make coverage
```

## Writing Tests

### 1. Function-Based

We strictly use function-based tests (no `class TestFoo:`).

### 2. Async Support

All tests involving I/O should be async:

```python
async def test_user_creation(client: AsyncClient) -> None:
    response = await client.post("/users", json={...})
    assert response.status_code == 201
```

### 3. Database Access

Use fixtures provided by `pytest-databases` and `advanced-alchemy`. Ensure tests are isolated (rollback or clean DB).

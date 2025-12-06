---
description: Testing with pattern compliance and coverage targets
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Task, mcp__pal__debug
---

# Testing Workflow

You are creating/running tests for: **$ARGUMENTS**

## Testing Standards for This Project

- **Framework**: pytest with pytest-asyncio
- **Coverage Target**: 90%+ for modified modules
- **Style**: Function-based tests (not class-based)
- **Parallel Execution**: Tests must work with `-n 2`
- **Database**: pytest-databases for isolated fixtures

---

## Checkpoint 0: Context Loading

**Load feature context:**

```bash
cat specs/active/{slug}/prd.md 2>/dev/null || echo "No PRD found, testing existing code"
cat specs/active/{slug}/tasks.md 2>/dev/null
```

**Identify files to test:**

```bash
git diff --name-only HEAD~5 | grep -E "\.py$"
# or for specific feature:
find app/domain/{feature}/ -name "*.py" -type f
```

**Output**: "✓ Checkpoint 0 complete - [N] files identified for testing"

---

## Checkpoint 1: Existing Test Analysis

**Find existing test patterns:**

```bash
ls tests/unit/
ls tests/integration/
cat tests/conftest.py | head -100
```

**Identify fixtures available:**

- Database session fixtures
- User fixtures
- Team fixtures
- Client fixtures

**Document test patterns found:**

```markdown
## Test Patterns in This Project

- Async tests use `pytest.mark.asyncio`
- Database tests use fixtures from conftest.py
- Services tested with repository mocks
- Controllers tested with test client
```

**Output**: "✓ Checkpoint 1 complete - Test patterns documented"

---

## Checkpoint 2: Unit Test Creation

**Create unit tests in `tests/unit/domain/{feature}/`:**

```python
from __future__ import annotations

import pytest

from app.domain.{feature}.services import YourService


class TestYourService:
    """Tests for YourService."""

    @pytest.mark.asyncio
    async def test_create_item(self, db_session) -> None:
        """Test creating an item."""
        service = YourService(session=db_session)
        result = await service.create({"name": "test"})
        assert result.name == "test"

    @pytest.mark.asyncio
    async def test_list_items(self, db_session) -> None:
        """Test listing items."""
        service = YourService(session=db_session)
        results = await service.list()
        assert isinstance(results, list)
```

**Test coverage patterns:**

1. **Happy path**: Normal operation
2. **Edge cases**: Empty data, null values
3. **Error cases**: Invalid input, not found
4. **Business logic**: Domain-specific rules

**Output**: "✓ Checkpoint 2 complete - Unit tests created"

---

## Checkpoint 3: Integration Test Creation

**Create integration tests in `tests/integration/`:**

```python
from __future__ import annotations

import pytest
from litestar.testing import AsyncTestClient


@pytest.mark.asyncio
async def test_list_endpoint(client: AsyncTestClient) -> None:
    """Test the list endpoint."""
    response = await client.get("/{feature}/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_endpoint(client: AsyncTestClient, auth_headers: dict) -> None:
    """Test creating via endpoint."""
    response = await client.post(
        "/{feature}/",
        json={"name": "test"},
        headers=auth_headers,
    )
    assert response.status_code == 201
```

**Output**: "✓ Checkpoint 3 complete - Integration tests created"

---

## Checkpoint 4: Run Tests

**Run unit tests:**

```bash
uv run pytest tests/unit/domain/{feature}/ -v
```

**Run integration tests:**

```bash
uv run pytest tests/integration/ -v -k "{feature}"
```

**Run all tests in parallel:**

```bash
make test
```

**If failures, debug and fix:**

Use `mcp__pal__debug` for complex failures:

```
mcp__pal__debug(
    step="Investigating test failure...",
    step_number=1,
    total_steps=3,
    next_step_required=true,
    findings="Test failed with...",
    hypothesis="The failure is caused by..."
)
```

**Output**: "✓ Checkpoint 4 complete - All tests pass"

---

## Checkpoint 5: Coverage Analysis

**Run coverage:**

```bash
make coverage
```

**Check coverage for specific module:**

```bash
uv run pytest tests/ --cov=app/domain/{feature} --cov-report=term-missing
```

**Target**: 90%+ coverage on modified modules

**If below target:**

1. Identify uncovered lines
2. Add tests for edge cases
3. Add tests for error handling
4. Re-run coverage

**Output**: "✓ Checkpoint 5 complete - Coverage: [N]%"

---

## Checkpoint 6: N+1 Query Detection (Database Operations)

**If feature includes database operations:**

```python
@pytest.mark.asyncio
async def test_no_n_plus_one_queries(client: AsyncTestClient, caplog) -> None:
    """Verify no N+1 queries occur."""
    # Enable SQL logging
    import logging
    caplog.set_level(logging.DEBUG, logger="sqlalchemy.engine")

    response = await client.get("/{feature}/")

    # Count queries
    query_count = sum(1 for r in caplog.records if "SELECT" in r.message)
    assert query_count <= 2, f"Too many queries: {query_count}"
```

**Output**: "✓ Checkpoint 6 complete - No N+1 queries detected"

---

## Checkpoint 7: Type Checking

**Run type checks on test files:**

```bash
uv run mypy tests/unit/domain/{feature}/
uv run pyright tests/unit/domain/{feature}/
```

**Ensure tests are properly typed.**

**Output**: "✓ Checkpoint 7 complete - Tests pass type checking"

---

## Checkpoint 8: Final Verification

**Run complete test suite:**

```bash
make test-all
```

**Run linting on tests:**

```bash
uv run ruff check tests/
```

**Verify parallel execution:**

```bash
uv run pytest tests/ -n 4 --quiet
```

**Output**: "✓ Checkpoint 8 complete - All verifications pass"

---

## Final Summary

```
Testing Phase Complete ✓

Feature: {slug}
Tests Created: [N] unit, [N] integration
Coverage: [N]%

Test Results:
- ✓ Unit tests pass
- ✓ Integration tests pass
- ✓ Parallel execution works
- ✓ Coverage target met (90%+)
- ✓ Type checking passes

Test Files:
- tests/unit/domain/{feature}/test_{feature}.py
- tests/integration/test_{feature}.py

Next: Run `/review {slug}` for final review
```

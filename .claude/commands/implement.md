---
description: Pattern-guided implementation from PRD
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Task, WebSearch, mcp__context7__resolve-library-id, mcp__context7__get-library-docs, mcp__pal__thinkdeep, mcp__pal__debug
---

# Pattern-Guided Implementation Workflow

You are implementing the feature: **$ARGUMENTS**

## Intelligence Layer (ACTIVATE FIRST)

1. **Load PRD context**: `specs/active/{slug}/prd.md`
2. **Load patterns**: `specs/active/{slug}/patterns/` and `specs/guides/patterns/`
3. **Load task list**: `specs/active/{slug}/tasks.md`
4. **Check MCP strategy**: `.claude/mcp-strategy.md`

---

## Checkpoint 0: Context Loading

**Required reads:**

```bash
cat specs/active/{slug}/prd.md
cat specs/active/{slug}/tasks.md
cat specs/active/{slug}/research/analysis.md
```

**Verify PRD exists and is complete.**

**Output**: "✓ Checkpoint 0 complete - PRD loaded, [N] tasks identified"

---

## Checkpoint 1: Pattern Deep Dive

Read 3-5 similar implementations identified in PRD:

For Litestar backend:
- Read existing controller in same domain
- Read existing service in same domain
- Read related models

For React/Inertia frontend:
- Read similar page component
- Read related UI components

**Document patterns in `specs/active/{slug}/tmp/patterns-found.md`:**

```markdown
## Patterns to Follow

### Controller Pattern
- Uses `@Controller` decorator with path
- Injects services via constructor
- Returns `InertiaResponse` for pages

### Service Pattern
- Extends `SQLAlchemyAsyncRepositoryService[Model]`
- Has `repository_type` class attribute
- Custom methods for business logic

### Repository Pattern
- Extends from advanced-alchemy base
- Uses model type parameter

### Frontend Pattern
- Page receives typed props
- Uses shadcn/ui components
- Follows resources/pages/{feature}/ structure
```

**Output**: "✓ Checkpoint 1 complete - Patterns documented"

---

## Checkpoint 2: Database Layer (if needed)

**Create models in `app/db/models/`:**

Follow existing model patterns:
- Use `__tablename__` with snake_case
- Include `__table_args__` if needed
- Use proper type hints with SQLAlchemy 2.0 syntax
- Export in `app/db/models/__init__.py`

**Create migration:**

```bash
uv run app database make-migrations
```

**Test migration:**

```bash
uv run app database upgrade
```

**Update task list:**
```bash
# Mark database tasks complete in specs/active/{slug}/tasks.md
```

**Output**: "✓ Checkpoint 2 complete - Database layer created"

---

## Checkpoint 3: Repository & Service Layer

**Create repository in `app/domain/{feature}/repositories.py`:**

```python
from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from app.db.models import YourModel

class YourModelRepository(SQLAlchemyAsyncRepository[YourModel]):
    model_type = YourModel
```

**Create service in `app/domain/{feature}/services.py`:**

```python
from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService
from app.db.models import YourModel
from app.domain.{feature}.repositories import YourModelRepository

class YourModelService(SQLAlchemyAsyncRepositoryService[YourModel]):
    repository_type = YourModelRepository
```

**Run tests to verify:**

```bash
make test
```

**Output**: "✓ Checkpoint 3 complete - Repository & service created"

---

## Checkpoint 4: Controller Layer

**Create controller in `app/domain/{feature}/controllers.py`:**

Follow Litestar + Inertia patterns:

```python
from litestar import Controller, get, post
from litestar.di import Provide
from litestar_vite.inertia import InertiaResponse

class YourController(Controller):
    path = "/{feature}"

    @get("/")
    async def list(self, service: YourModelService) -> InertiaResponse:
        items = await service.list()
        return InertiaResponse(
            component="{Feature}/List",
            props={"items": items}
        )
```

**Register in `app/server/core.py`:**

Add controller to `route_handlers` in `on_app_init`.

**Run linting:**

```bash
make pre-commit
make type-check
```

**Output**: "✓ Checkpoint 4 complete - Controller created and registered"

---

## Checkpoint 5: Frontend Layer

**Create Inertia page in `resources/pages/{feature}/`:**

```tsx
import { Head } from '@inertiajs/react'
import AppLayout from '@/layouts/app-layout'

interface Props {
  items: Item[]
}

export default function List({ items }: Props) {
  return (
    <AppLayout>
      <Head title="Feature" />
      {/* Component content */}
    </AppLayout>
  )
}
```

**Create supporting components in `resources/components/{feature}/`:**

Use shadcn/ui patterns from existing components.

**Run frontend linting:**

```bash
npx biome check resources/
```

**Output**: "✓ Checkpoint 5 complete - Frontend created"

---

## Checkpoint 6: Integration Testing

**Run full test suite:**

```bash
make test
```

**Run type checking:**

```bash
make type-check
```

**Run all linting:**

```bash
make lint
```

**If failures, fix and re-run.**

**Output**: "✓ Checkpoint 6 complete - All tests and linting pass"

---

## Checkpoint 7: Unit Tests

**Create tests in `tests/unit/domain/{feature}/`:**

Follow pytest patterns:
- Function-based tests
- Async where needed
- Use fixtures from `tests/conftest.py`

**Target 90%+ coverage on new code:**

```bash
make coverage
```

**Update task list:**
```bash
# Mark test tasks complete in specs/active/{slug}/tasks.md
```

**Output**: "✓ Checkpoint 7 complete - Unit tests created, [N]% coverage"

---

## Checkpoint 8: Documentation & Patterns

**Document any new patterns in `specs/active/{slug}/tmp/new-patterns.md`:**

```markdown
## New Patterns Discovered

### Pattern Name
- Description
- When to use
- Example code reference
```

**Update RECOVERY.md with implementation status.**

**Output**: "✓ Checkpoint 8 complete - Documentation updated"

---

## Checkpoint 9: Final Verification

**Run complete quality gates:**

```bash
make lint
make test
make coverage
```

**Verify all task items are complete:**

```bash
cat specs/active/{slug}/tasks.md
```

**Git status check:**

```bash
git status
```

**Output**: "✓ Checkpoint 9 complete - All quality gates pass"

---

## Auto-Invoke Testing Agent

After implementation checkpoints, invoke testing agent:

```
Task(subagent_type="testing", prompt="Run comprehensive tests for {slug}...")
```

---

## Final Summary

```
Implementation Phase Complete ✓

Feature: {slug}
Files Modified: [list]
Tests: [pass/fail]
Coverage: [N]%

Quality Gates:
- ✓ make lint passes
- ✓ make test passes
- ✓ make type-check passes
- ✓ 90%+ coverage on new code

Patterns:
- ✓ Followed [N] existing patterns
- [New patterns documented: N]

Next: Run `/review {slug}` for final review
```

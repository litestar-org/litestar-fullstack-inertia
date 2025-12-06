# Pattern Library

This directory contains reusable patterns extracted from completed features.

## How Patterns Are Captured

1. During implementation, new patterns are documented in `tmp/new-patterns.md`
2. During review, patterns are extracted to this directory
3. Future PRD phases consult this library first

## Pattern Categories

### Architectural Patterns
- **Plugin patterns**: See `app/server/core.py` for `ApplicationCore` plugin
- **Service patterns**: Extend `SQLAlchemyAsyncRepositoryService` from advanced-alchemy
- **Controller patterns**: Domain-organized controllers in `app/domain/{feature}/controllers.py`

### Litestar Patterns
- **Inertia.js integration**: Controllers return Inertia responses, not JSON
- **Session auth**: Configured through `session_auth` guard
- **Dependency injection**: Use `Provide()` for service injection

### Type Handling Patterns
- Use `from __future__ import annotations` in all files
- Prefer `T | None` over `Optional[T]` (PEP 604)
- Use `TYPE_CHECKING` for import-only types

### Testing Patterns
- Function-based tests with pytest
- Async tests with `pytest-asyncio`
- Parallel execution with `pytest-xdist`
- Database fixtures with `pytest-databases`

### Frontend Patterns (React/Inertia)
- Pages in `resources/pages/` receive typed props
- Components use shadcn/ui from `resources/components/ui/`
- Layouts in `resources/layouts/`
- Use `router.visit()` for navigation

## Using Patterns

When starting a new feature:

1. Search this directory for similar patterns
2. Read pattern documentation before implementation
3. Follow established conventions
4. Add new patterns during review phase

## Key Files to Reference

| Pattern | Reference File |
|---------|---------------|
| Service layer | `app/domain/accounts/services.py` |
| Controllers | `app/domain/accounts/controllers.py` |
| Repositories | `app/domain/accounts/repositories.py` |
| Inertia pages | `resources/pages/dashboard.tsx` |
| React components | `resources/components/ui/*.tsx` |
| App configuration | `app/config.py` |

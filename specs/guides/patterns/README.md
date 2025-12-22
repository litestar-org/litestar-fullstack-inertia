# Project Patterns

Auto-extracted patterns from codebase for agent guidance.

## Architectural Patterns

- **Plugin Pattern**: `app.server.plugins` configures Litestar plugins (Vite, SQLAlchemy, Granian).
- **Domain-Driven Design**: Feature logic isolated in `app/domain/{feature}/` (controllers, services, repositories).
- **Inertia Controller**: Controllers return `InertiaRedirect` or dicts for Inertia pages.

## Code Patterns

- **Service Layer**: Inherit from `SQLAlchemyAsyncRepositoryService` for DB operations.
- **Repository Layer**: Inherit from `SQLAlchemyAsyncRepository`.
- **Dependency Injection**: Use `litestar.di.Provide` for services in controllers.
- **Signals**: Use `litestar.events` for decoupled logic (e.g., `user_created` event).

## Testing Patterns

- **Fixture-Based**: Use `conftest.py` fixtures for setup.
- **Async Testing**: `pytest.mark.anyio` for async tests.
- **Settings Patching**: `_patch_settings` fixture in `conftest.py` ensures test isolation.

---

*This index is maintained automatically by agents during feature development.*

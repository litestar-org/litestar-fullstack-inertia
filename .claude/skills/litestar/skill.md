# Litestar Framework Skill

## Quick Reference

### Controller

```python
from litestar import Controller, get, post, delete, patch, put
from litestar.di import Provide
from litestar.params import Parameter
from litestar_vite.inertia import InertiaResponse

class FeatureController(Controller):
    path = "/feature"
    tags = ["Feature"]

    @get("/")
    async def list(self, service: FeatureService) -> InertiaResponse:
        items = await service.list()
        return InertiaResponse(
            component="Feature/List",
            props={"items": items}
        )

    @get("/{item_id:uuid}")
    async def show(
        self,
        item_id: UUID,
        service: FeatureService,
    ) -> InertiaResponse:
        item = await service.get(item_id)
        return InertiaResponse(
            component="Feature/Show",
            props={"item": item}
        )

    @post("/")
    async def create(
        self,
        data: CreateDTO,
        service: FeatureService,
    ) -> InertiaResponse:
        item = await service.create(data)
        return InertiaResponse(
            component="Feature/Show",
            props={"item": item}
        )
```

### Dependency Injection

```python
from litestar.di import Provide

def provide_service(db_session: AsyncSession) -> FeatureService:
    return FeatureService(session=db_session)

# In controller
dependencies = {"service": Provide(provide_service)}
```

### Guards

```python
from litestar.connection import ASGIConnection
from litestar.handlers import BaseRouteHandler

async def require_auth(
    connection: ASGIConnection,
    _: BaseRouteHandler,
) -> None:
    if not connection.user:
        raise PermissionDeniedException("Authentication required")
```

### Inertia Response

```python
from litestar_vite.inertia import InertiaResponse

# Page response
return InertiaResponse(
    component="Feature/List",  # Maps to resources/pages/Feature/List.tsx
    props={"items": items, "meta": meta}
)

# Redirect
return InertiaResponse.redirect("/feature")
```

## Project Patterns

### Controller Location
`app/domain/{feature}/controllers.py`

### Service Location
`app/domain/{feature}/services.py`

### Registering Controllers
In `app/server/core.py`:
```python
app_config.route_handlers.extend([
    FeatureController,
])
```

## Context7 Lookup

```python
mcp__context7__get-library-docs(
    context7CompatibleLibraryID="/litestar-org/litestar",
    topic="controllers",  # or: routing, di, guards, middleware
    mode="code"
)
```

## Related Files

- `app/server/core.py` - Controller registration
- `app/domain/accounts/controllers.py` - Controller example
- `app/domain/accounts/guards.py` - Guard example
- `app/lib/dependencies.py` - Dependency providers

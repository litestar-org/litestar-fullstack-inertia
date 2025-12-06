# Inertia.js Skill (Litestar Integration)

## Quick Reference

### Backend Pattern (This Project's Style)

The `component` kwarg in route decorators is the preferred pattern:

```python
from litestar import Controller, get, post, patch, delete
from litestar_vite.inertia import InertiaRedirect

class FeatureController(Controller):
    path = "/feature"

    # Return dict for page props - component specified in decorator
    @get(component="feature/list", path="/", name="feature.list")
    async def list(self, service: FeatureService) -> dict:
        """List feature items."""
        items = await service.list()
        return {"items": items}

    # Can also return a schema directly
    @get(component="feature/show", path="/{item_id:uuid}", name="feature.show")
    async def show(self, item_id: UUID, service: FeatureService) -> FeatureSchema:
        """Show single item."""
        item = await service.get(item_id)
        return service.to_schema(item, schema_type=FeatureSchema)

    # POST with component for form display
    @post(component="feature/create", path="/", name="feature.create")
    async def create(
        self,
        request: Request,
        data: CreateSchema,
        service: FeatureService,
    ) -> InertiaRedirect:
        """Create item and redirect."""
        item = await service.create(data.to_dict())
        flash(request, "Item created successfully.", category="info")
        return InertiaRedirect(request, request.url_for("feature.show", item_id=item.id))
```

### Redirects

```python
from litestar_vite.inertia import InertiaRedirect, InertiaExternalRedirect

# Internal redirect
return InertiaRedirect(request, request.url_for("dashboard"))

# External redirect (OAuth, external URLs)
return InertiaExternalRedirect(request, redirect_to="https://github.com/oauth/...")
```

### Sharing Data

```python
from litestar_vite.inertia import share

# Share data for the current request
share(
    request,
    "auth",
    {"isAuthenticated": True, "user": user_schema}
)
```

### Component Path Mapping

The `component` kwarg maps to `resources/pages/`:
- `component="feature/list"` → `resources/pages/feature/list.tsx`
- `component="auth/login"` → `resources/pages/auth/login.tsx`
- `component="dashboard"` → `resources/pages/dashboard.tsx`

### Frontend (React)

```tsx
import { Head, Link, router, usePage } from '@inertiajs/react'

// Page receives props from controller return value
interface Props {
  items: Item[]
}

export default function List({ items }: Props) {
  return (
    <>
      <Head title="Feature List" />
      <div className="container">
        {items.map(item => (
          <Link key={item.id} href={`/feature/${item.id}`}>
            {item.name}
          </Link>
        ))}
      </div>
    </>
  )
}
```

### Navigation

```tsx
import { Link, router } from '@inertiajs/react'

// Link component
<Link href="/feature/123">View Item</Link>

// Programmatic navigation
router.visit('/feature/123')

// With method
router.post('/feature', { name: 'test' })
```

### Forms

```tsx
import { useForm } from '@inertiajs/react'

function CreateForm() {
  const { data, setData, post, processing, errors } = useForm({
    name: '',
    description: '',
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    post('/feature')
  }

  return (
    <form onSubmit={handleSubmit}>
      <input
        value={data.name}
        onChange={e => setData('name', e.target.value)}
      />
      {errors.name && <span>{errors.name}</span>}
      <button disabled={processing}>Create</button>
    </form>
  )
}
```

## Project Patterns

### Controller Style
- Use `component` kwarg in route decorator
- Return `dict` or schema for page props
- Use `InertiaRedirect` for redirects after actions

### Page Location
`resources/pages/{component_path}.tsx`

### Example Controllers
- `app/domain/web/controllers.py` - Simple page controllers
- `app/domain/accounts/controllers.py` - Full CRUD with auth

### Inertia Configuration
`app/config.py`:
```python
inertia = InertiaConfig(
    root_template="site/index.html.j2",
    redirect_unauthorized_to="/login",
    extra_static_page_props={...},
    extra_session_page_props={...},
)
```

## Context7 Lookup

```python
mcp__context7__get-library-docs(
    context7CompatibleLibraryID="/inertiajs/inertia",
    topic="forms",  # or: links, routing, shared-data
    mode="code"
)
```

## Related Files

- `app/config.py` - Inertia configuration
- `app/domain/web/controllers.py` - Simple page controllers
- `app/domain/accounts/controllers.py` - Auth controllers with Inertia
- `resources/main.tsx` - App entry point
- `resources/pages/` - Page components
- `resources/layouts/` - Layout components

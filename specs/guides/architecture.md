# Architecture Guide

**Project**: Litestar Fullstack Inertia
**Version**: 2.0 | **Updated**: 2025-12-16

## Overview

This is a modern fullstack application using **Litestar** as the backend framework with **Inertia.js** for seamless SPA-like navigation and **React 19** for the frontend UI.

## Architecture Pattern

### Monolithic Fullstack with SPA Experience

```
┌─────────────────────────────────────────────────────────────┐
│                      Client (Browser)                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              React 19 + Inertia.js                    │  │
│  │  - shadcn/ui components                               │  │
│  │  - Tailwind CSS styling                               │  │
│  │  - TypeScript interfaces                              │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Inertia Protocol
                              │ (JSON or HTML)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Litestar Server                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                  Inertia Middleware                   │  │
│  │  - Handles X-Inertia requests                         │  │
│  │  - JSON responses for navigation                      │  │
│  │  - Full HTML for initial page loads                   │  │
│  └───────────────────────────────────────────────────────┘  │
│                              │                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                   Domain Layer                        │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │  │
│  │  │accounts │  │  teams  │  │  tags   │  │   web   │   │  │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘   │  │
│  └───────────────────────────────────────────────────────┘  │
│                              │                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                   Database Layer                      │  │
│  │  - SQLAlchemy 2.0 ORM                                 │  │
│  │  - advanced-alchemy services                          │  │
│  │  - Alembic migrations                                 │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      PostgreSQL + Redis                     │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

### Backend (`app/`)

```
app/
├── __init__.py          # CLI entry point (run_cli)
├── config.py            # All configuration classes
├── cli.py               # CLI commands
│
├── domain/              # Domain modules (feature-based)
│   ├── accounts/        # User authentication & profiles
│   │   ├── controllers.py   # API/Inertia endpoints
│   │   ├── services.py      # Business logic
│   │   ├── repositories.py  # Data access
│   │   ├── schemas.py       # Pydantic models
│   │   └── guards.py        # Auth guards
│   ├── teams/           # Multi-tenant team management
│   ├── tags/            # Tagging system
│   └── web/             # Inertia page controllers
│       └── controllers.py   # Root pages (landing, about, etc.)
│
├── db/
│   ├── models/          # SQLAlchemy ORM models
│   │   ├── base.py      # Base model with audit fields
│   │   ├── user.py      # User model
│   │   ├── team.py      # Team model
│   │   └── ...
│   └── migrations/      # Alembic migrations
│       └── versions/
│
├── lib/                 # Shared utilities
│   ├── log.py           # Logging configuration
│   ├── settings.py      # App settings
│   └── ...
│
├── server/
│   ├── core.py          # ApplicationCore plugin
│   └── plugins.py       # Plugin instances (db, cache, etc.)
│
└── utils/               # Utility functions
```

### Frontend (`resources/`)

```
resources/
├── main.tsx             # App entry point (createInertiaApp)
├── app.css              # Global styles + Tailwind
│
├── pages/               # Inertia page components
│   ├── landing.tsx      # Public landing page
│   ├── dashboard.tsx    # Authenticated dashboard
│   ├── auth/            # Auth pages
│   │   ├── login.tsx
│   │   └── register.tsx
│   ├── profile/         # User profile pages
│   │   ├── index.tsx
│   │   └── settings.tsx
│   └── team/            # Team management
│
├── components/
│   ├── ui/              # shadcn/ui components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   └── ...
│   └── shared/          # App-specific components
│
├── layouts/
│   ├── app-layout.tsx   # Authenticated layout
│   └── guest-layout.tsx # Public layout
│
├── hooks/               # Custom React hooks
│   └── use-toast.ts
│
└── lib/
    └── utils.ts         # Utility functions (cn, etc.)
```

## Key Patterns

### 1. Controller Pattern (Backend)

Controllers handle HTTP requests and return Inertia responses:

```python
from litestar import Controller, get, post
from litestar_vite.inertia import InertiaRedirect

class FeatureController(Controller):
    path = "/feature"

    @get(component="feature/index", name="feature.index")
    async def index(self, service: FeatureService) -> dict:
        """Inertia page - returns props as dict."""
        items = await service.list()
        return {"items": items}

    @post(path="/", name="feature.create")
    async def create(
        self,
        request: Request,
        data: CreateSchema,
        service: FeatureService,
    ) -> InertiaRedirect:
        """Handle form submission - redirect on success."""
        await service.create(data.to_dict())
        return InertiaRedirect(request, request.url_for("feature.index"))
```

### 2. Service Pattern (Backend)

Services encapsulate business logic using advanced-alchemy:

```python
from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService
from app.db.models import FeatureModel
from app.domain.feature.repositories import FeatureRepository

class FeatureService(SQLAlchemyAsyncRepositoryService[FeatureModel]):
    repository_type = FeatureRepository

    async def create_with_validation(self, data: dict) -> FeatureModel:
        """Custom business logic."""
        # Validation, transformation, etc.
        return await self.create(data)
```

### 3. Repository Pattern (Backend)

Repositories handle data access:

```python
from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from app.db.models import FeatureModel

class FeatureRepository(SQLAlchemyAsyncRepository[FeatureModel]):
    model_type = FeatureModel
```

### 4. Page Component Pattern (Frontend)

Inertia pages receive typed props from controllers:

```tsx
import { Head } from '@inertiajs/react'
import AppLayout from '@/layouts/app-layout'

interface Props {
  items: Item[]
  user: User
}

export default function Index({ items, user }: Props) {
  return (
    <AppLayout>
      <Head title="Feature List" />
      <div className="space-y-4">
        {items.map(item => (
          <Card key={item.id}>{item.name}</Card>
        ))}
      </div>
    </AppLayout>
  )
}
```

### 5. Form Handling Pattern (Frontend)

Using Inertia's useForm hook:

```tsx
import { useForm } from '@inertiajs/react'

export default function CreateForm() {
  const { data, setData, post, processing, errors } = useForm({
    name: '',
    email: '',
  })

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    post('/feature')
  }

  return (
    <form onSubmit={submit}>
      <Input
        value={data.name}
        onChange={e => setData('name', e.target.value)}
        error={errors.name}
      />
      <Button type="submit" disabled={processing}>
        Create
      </Button>
    </form>
  )
}
```

## Data Flow

### Page Navigation

```
1. User clicks link/button
2. Inertia intercepts navigation
3. XHR request with X-Inertia header
4. Litestar controller returns props (JSON)
5. Inertia swaps page component with new props
6. URL updated without full page reload
```

### Form Submission

```
1. User submits form
2. Inertia posts data to endpoint
3. Controller validates and processes
4. On success: InertiaRedirect
5. Inertia follows redirect, fetches new page
6. Page component updates
```

## Configuration

### Key Files

| File | Purpose |
|------|---------|
| `app/config.py` | All app configuration (DB, cache, Inertia) |
| `app/server/core.py` | ApplicationCore plugin, route registration |
| `vite.config.ts` | Vite build configuration |
| `components.json` | shadcn/ui component configuration |

### Environment Variables

```bash
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://...
SECRET_KEY=...
VITE_DEV_MODE=true  # Enable Vite HMR
```

## Testing Strategy

### Backend Tests

- **Unit tests**: Service logic, utilities
- **Integration tests**: Controller endpoints with database
- **Use pytest-asyncio** for async operations
- **Factory pattern** for test data

### Frontend Tests

- Component tests with React Testing Library
- E2E tests with Playwright (optional)

## Performance Considerations

1. **Database**: Use eager loading to avoid N+1 queries
2. **Caching**: Redis for session and query caching
3. **Frontend**: Code splitting via Vite
4. **Assets**: Vite handles bundling and optimization

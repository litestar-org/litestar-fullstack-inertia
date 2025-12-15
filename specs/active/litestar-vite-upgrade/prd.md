# PRD: Litestar-Vite Alpha 6 Upgrade

## Intelligence Context

- **Complexity**: Complex (10+ checkpoints)
- **Similar Features Analyzed**:
  - `litestar-vite/examples/react-inertia/` - New implementation pattern
  - `litestar-fullstack-spa/` - Features to adopt
  - Current `app/config.py` - Migration source
- **Patterns to Follow**:
  - Unified ViteConfig with nested sub-configs
  - Hybrid mode for template-less Inertia
  - TypeGenConfig for route/SDK generation
- **Tool Used for Analysis**: `mcp__pal__planner` (3-step structured planning)

---

## Problem Statement

The litestar-fullstack-inertia project was designed to be a showcase application demonstrating the integration of Litestar with Inertia.js. However, the current implementation uses an outdated configuration pattern from earlier litestar-vite versions that:

1. **Requires separate plugins**: VitePlugin and InertiaPlugin must be registered separately
2. **Depends on Jinja templates**: Uses `site/index.html.j2` for Inertia root template
3. **Lacks type generation**: No automatic generation of routes.ts, OpenAPI schema, or SDK
4. **Uses deprecated configuration API**: Flat ViteConfig instead of nested PathConfig/RuntimeConfig/TypeGenConfig

The latest litestar-vite alpha 6 release introduces a fundamentally improved architecture that simplifies configuration, enables powerful type generation features, and removes the Jinja2 dependency for Inertia applications.

---

## Goals & Success Metrics

### Primary Goals

1. **Modernize Configuration**: Migrate from flat ViteConfig to nested sub-config architecture
2. **Enable Hybrid Mode**: Replace Jinja templates with HtmlTransformer for template-less Inertia
3. **Enable Type Generation**: Generate routes.ts, openapi.json, and SDK automatically
4. **Simplify Plugin Architecture**: Use single VitePlugin instead of VitePlugin + InertiaPlugin
5. **Showcase Best Practices**: Serve as reference implementation for Litestar + Inertia.js

### Success Metrics

| Metric | Target |
|--------|--------|
| Test pass rate | 100% |
| Type checking | mypy + pyright pass |
| Lint status | All checks pass |
| Routes generated | Valid routes.ts produced |
| OpenAPI schema | Valid openapi.json produced |
| Page render | All existing pages render correctly |
| Auth flows | Login, register, OAuth all functional |
| Dev experience | HMR works, types available |

---

## Acceptance Criteria

### Configuration Migration

- [ ] ViteConfig uses nested PathConfig, RuntimeConfig, TypeGenConfig, InertiaConfig
- [ ] Single VitePlugin handles both Vite and Inertia functionality
- [ ] InertiaPlugin import and instance removed
- [ ] TemplateConfig for Inertia removed (not needed in hybrid mode)
- [ ] ViteSettings simplified to essential parameters only

### Template Migration

- [ ] resources/index.html created with proper Inertia structure
- [ ] Mode auto-detected as "hybrid" from Inertia + index.html presence
- [ ] Jinja template at app/domain/web/templates/site/index.html.j2 removed
- [ ] Flash messages work in hybrid mode (via shared data or alternative)

### Type Generation

- [ ] TypeGenConfig enabled with output at src/lib/generated/
- [ ] routes.ts generated with typed route helpers
- [ ] routes.json generated with route metadata
- [ ] openapi.json generated with full API schema
- [ ] @hey-api/openapi-ts configured for SDK generation
- [ ] npm script added for type regeneration

### Frontend Updates

- [ ] vite.config.ts updated for new plugin structure
- [ ] package.json includes @hey-api/openapi-ts dependency
- [ ] openapi-ts.config.ts created for SDK configuration
- [ ] litestar-vite-plugin updated to latest version

### Quality Gates

- [ ] `make test` passes
- [ ] `make lint` passes (includes pre-commit + type-check)
- [ ] `npx biome check resources/` passes
- [ ] 90%+ coverage for modified modules

### Functionality Preservation

- [ ] Login flow works (session-based auth)
- [ ] Registration flow works
- [ ] OAuth flows work (GitHub, Google)
- [ ] Dashboard accessible to authenticated users
- [ ] Profile editing works
- [ ] Flash messages display correctly
- [ ] CSRF protection functional

---

## Technical Approach

### Overview Architecture

```
+------------------+     +------------------+     +-------------------+
|   VitePlugin     |---->|   ViteConfig     |---->|   PathConfig      |
|   (Single)       |     |   (Root)         |     |   RuntimeConfig   |
+------------------+     +------------------+     |   TypeGenConfig   |
                                |                 |   InertiaConfig   |
                                |                 +-------------------+
                                v
                         +------------------+
                         |  HtmlTransformer |
                         |  (Hybrid Mode)   |
                         +------------------+
                                |
                                v
                         +------------------+
                         |  index.html      |
                         |  (No Jinja)      |
                         +------------------+
```

### Backend Implementation

#### File: app/config.py

**Before (Current)**:
```python
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.template import TemplateConfig
from litestar_vite import ViteConfig
from litestar_vite.inertia import InertiaConfig

vite = ViteConfig(
    bundle_dir=settings.vite.BUNDLE_DIR,
    resource_dir=settings.vite.RESOURCE_DIR,
    use_server_lifespan=settings.vite.USE_SERVER_LIFESPAN,
    dev_mode=settings.vite.DEV_MODE,
    hot_reload=settings.vite.HOT_RELOAD,
    is_react=settings.vite.ENABLE_REACT_HELPERS,
    port=settings.vite.PORT,
    host=settings.vite.HOST,
)
inertia = InertiaConfig(
    root_template="site/index.html.j2",
    redirect_unauthorized_to="/login",
    extra_static_page_props={...},
    extra_session_page_props={"currentTeam"},
)
templates = TemplateConfig(engine=JinjaTemplateEngine(directory=settings.vite.TEMPLATE_DIR))
```

**After (Target)**:
```python
from pathlib import Path
from litestar_vite import (
    VitePlugin,
    ViteConfig,
    PathConfig,
    RuntimeConfig,
    TypeGenConfig,
    InertiaConfig,
)

from app.lib.settings import get_settings, BASE_DIR

settings = get_settings()

vite = VitePlugin(
    config=ViteConfig(
        dev_mode=settings.vite.DEV_MODE,
        paths=PathConfig(
            root=BASE_DIR.parent,
            resource_dir=Path("resources"),
            bundle_dir=Path("public"),
            asset_url=settings.vite.ASSET_URL,
        ),
        runtime=RuntimeConfig(
            host=settings.vite.HOST,
            port=settings.vite.PORT,
            is_react=True,
        ),
        inertia=InertiaConfig(
            root_template="index.html",
            redirect_unauthorized_to="/login",
            extra_static_page_props={
                "canResetPassword": True,
                "hasTermsAndPrivacyPolicyFeature": True,
                "mustVerifyEmail": True,
            },
            extra_session_page_props={"currentTeam"},
        ),
        types=TypeGenConfig(
            output=BASE_DIR.parent / "src" / "lib" / "generated",
            generate_zod=True,
            generate_sdk=True,
            generate_routes=True,
        ),
    )
)
```

#### File: app/server/plugins.py

**Before**:
```python
from litestar_vite import VitePlugin
from litestar_vite.inertia import InertiaPlugin

vite = VitePlugin(config=config.vite)
inertia = InertiaPlugin(config=config.inertia)
```

**After**:
```python
from app import config

# VitePlugin is now created in config.py with Inertia integrated
vite = config.vite
# Remove: inertia = InertiaPlugin(config=config.inertia)
```

#### File: app/server/core.py

**Changes**:
- Remove `plugins.inertia` from plugin list
- Remove `config.templates` assignment (if not needed elsewhere)
- Update plugin order if necessary

#### File: app/lib/settings.py

**Simplify ViteSettings**:
```python
@dataclass
class ViteSettings:
    """Vite configuration settings."""

    DEV_MODE: bool = field(
        default_factory=lambda: os.getenv("VITE_DEV_MODE", "False") in TRUE_VALUES,
    )
    HOST: str = field(default_factory=lambda: os.getenv("VITE_HOST", "127.0.0.1"))
    PORT: int = field(default_factory=lambda: int(os.getenv("VITE_PORT", "5173")))
    ASSET_URL: str = field(default_factory=lambda: os.getenv("ASSET_URL", "/static/"))

    # Removed deprecated settings:
    # - HOT_RELOAD (derived from DEV_MODE)
    # - USE_SERVER_LIFESPAN (auto-managed)
    # - ENABLE_REACT_HELPERS (now is_react in RuntimeConfig)
    # - BUNDLE_DIR (moved to code)
    # - RESOURCE_DIR (moved to code)
    # - TEMPLATE_DIR (no longer needed)
```

### Frontend Implementation

#### File: resources/index.html (New)

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/png" href="/favicon.png" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title inertia>Litestar Fullstack Inertia</title>
  </head>
  <body>
    <div id="app" data-page="{{ page | tojson | e }}"></div>
    <script type="module" src="/resources/main.tsx"></script>
  </body>
</html>
```

Key elements:
- `<title inertia>` enables Inertia title management
- `data-page="{{ page | tojson | e }}"` is the injection point for page data
- Script src points to resources/main.tsx

#### File: vite.config.ts (Updated)

```typescript
import path from "node:path"
import tailwindcss from "@tailwindcss/vite"
import react from "@vitejs/plugin-react"
import litestar from "litestar-vite-plugin"
import { defineConfig } from "vite"

export default defineConfig({
  plugins: [
    tailwindcss(),
    react(),
    litestar({
      input: ["resources/main.tsx"],
    }),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "resources"),
    },
  },
})
```

#### File: package.json (Updated)

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build && tsc -b --noEmit",
    "preview": "vite preview",
    "generate-types": "openapi-ts --config openapi-ts.config.ts"
  },
  "dependencies": {
    // Existing dependencies...
    "zod": "^4.0.0"
  },
  "devDependencies": {
    "litestar-vite-plugin": "latest",
    "@hey-api/openapi-ts": "^0.88.0",
    "@tailwindcss/vite": "^4.1.17",
    // Existing dev dependencies...
  }
}
```

#### File: openapi-ts.config.ts (New)

```typescript
import { defineConfig } from "@hey-api/openapi-ts"

export default defineConfig({
  input: "./src/lib/generated/openapi.json",
  output: "./src/lib/generated/api",
  plugins: [
    "@hey-api/typescript",
    "@hey-api/schemas",
    "@hey-api/sdk",
    "@hey-api/client-axios"
  ],
})
```

### Database

No database migrations required. This is a configuration-only change.

---

## Testing Strategy

### Unit Tests

**Backend tests to add/modify**:
- Test ViteConfig creation with new structure
- Test mode auto-detection (hybrid mode)
- Test type generation output paths

**Frontend tests** (if applicable):
- Test route() helper function
- Test generated API client types

### Integration Tests

**Controller tests**:
- Verify InertiaRedirect works in hybrid mode
- Test flash message handling
- Test session-based authentication flow
- Test OAuth callback flows

**Page rendering tests**:
- Verify all pages render without errors
- Check CSRF token injection
- Verify page props are correctly passed

### Manual Testing Checklist

1. **Authentication**:
   - [ ] Login with username/password
   - [ ] Logout
   - [ ] Register new account
   - [ ] GitHub OAuth login
   - [ ] Google OAuth login

2. **Navigation**:
   - [ ] Landing page loads
   - [ ] Dashboard loads (authenticated)
   - [ ] Profile page loads
   - [ ] About page loads
   - [ ] Privacy/Terms pages load

3. **Functionality**:
   - [ ] Flash messages appear
   - [ ] Form submissions work
   - [ ] Profile updates save
   - [ ] Password changes work

4. **Development Experience**:
   - [ ] HMR works (modify component, see update)
   - [ ] Type generation produces files
   - [ ] Generated types are accurate

---

## Pattern Compliance

### Follows Existing Patterns

1. **Service Pattern**: No changes to service layer
2. **Repository Pattern**: No changes to repository layer
3. **Controller Pattern**: Controllers continue using `component` kwarg

### New Patterns Introduced

1. **Unified ViteConfig**: Single configuration object with nested sub-configs
2. **TypeGenConfig Pattern**: Automatic type generation configuration
3. **Hybrid Mode Pattern**: Template-less Inertia with HtmlTransformer

---

## Migration Path

### Phase 1: Backend Configuration (Critical)

```
app/config.py
├── Update imports
├── Restructure ViteConfig
├── Create VitePlugin instance
└── Remove InertiaConfig/TemplateConfig

app/server/plugins.py
├── Reference config.vite
└── Remove InertiaPlugin

app/server/core.py
├── Update plugin list
└── Remove template config assignment

app/lib/settings.py
└── Simplify ViteSettings
```

### Phase 2: Template Migration (High Priority)

```
resources/
└── index.html (create)

app/domain/web/templates/site/
└── index.html.j2 (delete)
```

### Phase 3: Frontend Restructuring (High Priority)

```
src/lib/generated/ (create)
├── routes.ts (auto-generated)
├── routes.json (auto-generated)
├── openapi.json (auto-generated)
└── api/ (SDK output)

vite.config.ts (update)
package.json (update)
openapi-ts.config.ts (create)
```

### Phase 4: Cleanup (Medium Priority)

```
app/domain/web/controllers.py (evaluate)
├── Keep essential routes
└── Remove template-dependent logic

app/domain/web/templates/ (clean)
└── Remove unused templates
```

### Phase 5: Validation (Critical)

```
make test
make lint
npx biome check resources/
Manual testing of all flows
```

---

## Risk Assessment

### High Risk Items

| Risk | Impact | Mitigation |
|------|--------|------------|
| Auth flow breaks | Users cannot login | Test after each config change |
| Template migration errors | 500 errors on pages | Test hybrid mode in isolation |
| Session handling changes | Lost sessions | Verify session middleware order |

### Medium Risk Items

| Risk | Impact | Mitigation |
|------|--------|------------|
| Flash messages fail | No user feedback | Test FlashPlugin compatibility |
| OAuth callbacks break | OAuth login fails | Test OAuth flows explicitly |
| Type generation fails | No typed routes | Verify paths and config |

### Low Risk Items

| Risk | Impact | Mitigation |
|------|--------|------------|
| Styling differences | Visual changes | Compare before/after |
| Minor type errors | IDE warnings | Fix incrementally |

---

## Dependencies

### Python Dependencies

```toml
[project.dependencies]
litestar-vite = ">=0.7.0a6"  # Update to latest alpha
```

### NPM Dependencies

```json
{
  "devDependencies": {
    "litestar-vite-plugin": "latest",
    "@hey-api/openapi-ts": "^0.88.0",
    "@tailwindcss/vite": "^4.1.17"
  },
  "dependencies": {
    "zod": "^4.0.0"
  }
}
```

---

## Future Considerations

After completing this migration, consider:

1. **Tailwind 4 Full Migration**: Currently uses Tailwind 3, could migrate to 4
2. **TanStack Query Integration**: For better data fetching patterns
3. **PostgreSQL SAQ Broker**: More reliable than Redis for task queues
4. **Problem Details Plugin**: Standardized error responses

---

## Appendix: File Change Summary

### Files to Create

| File | Purpose |
|------|---------|
| resources/index.html | Inertia root template |
| src/lib/generated/ | Type generation output folder |
| openapi-ts.config.ts | SDK generation config |

### Files to Modify

| File | Change Type |
|------|-------------|
| app/config.py | Major restructure |
| app/server/plugins.py | Simplify |
| app/server/core.py | Update plugin list |
| app/lib/settings.py | Simplify ViteSettings |
| vite.config.ts | Update plugin config |
| package.json | Add dependencies |
| pyproject.toml | Update litestar-vite |

### Files to Delete

| File | Reason |
|------|--------|
| app/domain/web/templates/site/index.html.j2 | Replaced by resources/index.html |

### Files to Evaluate

| File | Decision Needed |
|------|-----------------|
| app/domain/web/controllers.py | Which routes to keep? |
| app/domain/web/templates/email/ | Keep for email templates |

---

## Detailed Implementation Notes

### Understanding the New ViteConfig Architecture

The new litestar-vite alpha 6 configuration system is built around composable dataclasses. Each sub-configuration handles a specific concern:

#### PathConfig Deep Dive

PathConfig manages all file system paths for the Vite integration:

```python
@dataclass
class PathConfig:
    root: Path              # Project root directory
    bundle_dir: Path        # Where Vite outputs built assets
    resource_dir: Path      # TypeScript/JavaScript source files
    public_dir: Path        # Static public assets (served as-is)
    manifest_name: str      # Name of Vite manifest file
    hot_file: str           # Hot reload indicator file
    asset_url: str          # Base URL for asset references
    ssr_output_dir: Path    # SSR output (if applicable)
```

For this project:
- `root`: Project root (parent of app/)
- `bundle_dir`: `public/` (where built assets go)
- `resource_dir`: `resources/` (where TypeScript source lives)
- `asset_url`: `/static/` (URL prefix for assets)

#### RuntimeConfig Deep Dive

RuntimeConfig controls runtime behavior of the Vite integration:

```python
@dataclass
class RuntimeConfig:
    dev_mode: bool           # Enable dev server with HMR
    proxy_mode: str | None   # How to proxy requests
    host: str                # Dev server host
    port: int                # Dev server port
    protocol: str            # http or https
    executor: str            # node, bun, deno, etc.
    is_react: bool           # Enable React Fast Refresh
    ssr_enabled: bool        # Enable SSR
    spa_handler: bool        # Auto-register SPA catch-all
    http2: bool              # Enable HTTP/2 for proxy
    start_dev_server: bool   # Auto-start dev server
```

For this project:
- `dev_mode`: From environment variable
- `host`: "127.0.0.1" or from env
- `port`: 5173 or from env
- `is_react`: True (we're using React)

#### TypeGenConfig Deep Dive

TypeGenConfig controls automatic code generation:

```python
@dataclass
class TypeGenConfig:
    output: Path             # Output directory for generated files
    openapi_path: Path       # Where to write openapi.json
    routes_path: Path        # Where to write routes.json
    routes_ts_path: Path     # Where to write routes.ts
    generate_zod: bool       # Generate Zod schemas
    generate_sdk: bool       # Generate API SDK
    generate_routes: bool    # Generate routes.ts
    watch_patterns: list     # Patterns to watch for regeneration
```

For this project:
- `output`: `src/lib/generated/`
- `generate_zod`: True (for form validation)
- `generate_sdk`: True (for API client)
- `generate_routes`: True (for typed routes)

### Understanding Hybrid Mode

Hybrid mode is the key innovation in litestar-vite alpha 6 for Inertia.js applications. Here's how it differs from the traditional approach:

#### Traditional (Template) Mode

```
Request -> Litestar -> Controller -> Jinja2 Template -> Response
                                          |
                                    Render index.html.j2
                                          |
                                    Inject page data
```

Problems:
- Jinja2 dependency
- Template compilation overhead
- Complex template syntax
- Harder to debug

#### Hybrid Mode (New)

```
Request -> Litestar -> Controller -> HtmlTransformer -> Response
                                          |
                                    Static index.html
                                          |
                                    Inject page data via DOM
```

Benefits:
- No Jinja2 dependency
- Simpler static HTML
- Faster response times
- Easier debugging
- Better alignment with frontend patterns

The HtmlTransformer works by:
1. Reading static index.html at startup
2. Parsing the DOM to find the app element
3. Injecting page data as `data-page` attribute
4. Optionally injecting CSRF token as `window.__LITESTAR_CSRF__`

### WebController Evaluation

The current WebController needs evaluation for the showcase app:

#### Routes to Keep

1. **home** (`/`): Redirect logic is useful
   - Redirect authenticated users to dashboard
   - Redirect unauthenticated to landing
   - Keep as-is

2. **landing** (`/landing/`): Marketing page
   - Core showcase feature
   - Keep as-is

3. **dashboard** (`/dashboard/`): User dashboard
   - Core feature
   - Keep as-is

4. **privacy-policy** (`/privacy-policy/`): Legal requirement
   - Keep as-is

5. **terms-of-service** (`/terms-of-service/`): Legal requirement
   - Keep as-is

#### Routes to Evaluate

1. **about** (`/about/`): May not be needed for showcase
   - Consider removing or simplifying

2. **favicon** (`/favicon.ico/`): Static file serving
   - May be handled by VitePlugin automatically
   - Test and remove if redundant

### Flash Message Handling in Hybrid Mode

Flash messages require special attention in hybrid mode. The FlashPlugin traditionally works with Jinja2 templates. In hybrid mode, we have options:

#### Option 1: Inertia Shared Data

Use Inertia's shared data mechanism:

```python
from litestar_vite.inertia import share

@post(component="auth/login", name="login.check", path="/login/")
async def login(self, request, data, users_service):
    user = await users_service.authenticate(data.username, data.password)
    request.set_session({"user_id": user.email})
    share(request, "flash", {"message": "Welcome!", "category": "info"})
    return InertiaRedirect(request, request.url_for("dashboard"))
```

Frontend handles via `usePage()`:

```tsx
const { flash } = usePage().props
useEffect(() => {
  if (flash?.message) {
    toast(flash.message, { type: flash.category })
  }
}, [flash])
```

#### Option 2: Session-Based Flash

Continue using FlashPlugin with session storage, read on frontend:

```tsx
const { errors, flash } = usePage().props
// FlashPlugin injects into page props automatically
```

### CSRF Token Handling

The new SPAConfig handles CSRF token injection:

```python
@dataclass
class SPAConfig:
    inject_csrf: bool = True
    csrf_var_name: str = "__LITESTAR_CSRF__"
    app_selector: str = "#app"
```

This injects a script into the HTML:

```html
<script>window.__LITESTAR_CSRF__ = "token-value";</script>
```

Frontend can read this for AJAX requests:

```typescript
import axios from 'axios'

const csrfToken = (window as any).__LITESTAR_CSRF__
axios.defaults.headers.common['X-XSRF-TOKEN'] = csrfToken
```

### Generated Routes Usage

The generated routes.ts provides type-safe route helpers:

```typescript
// Generated routes.ts
export const routes = {
  "login": "/login/",
  "dashboard": "/dashboard/",
  "profile.show": "/profile/",
  "users:list": "/api/users",
  "users:get": "/api/users/{user_id}",
}

export function route(name: RouteName, params?: RouteParams): string {
  // Type-safe URL generation
}
```

Usage in components:

```tsx
import { route } from '@/lib/generated/routes'

// Type-safe navigation
router.visit(route('dashboard'))
router.visit(route('users:get', { user_id: 'uuid-here' }))
```

### Generated SDK Usage

The @hey-api/openapi-ts generates a type-safe API client:

```typescript
// Usage
import { UsersService } from '@/lib/generated/api'

// Type-safe API calls
const users = await UsersService.listUsers()
const user = await UsersService.getUser({ userId: 'uuid' })
```

### Development Workflow After Migration

1. **Start backend**: `uv run app run`
2. **Start frontend**: `npm run dev` (auto-starts with backend if configured)
3. **Generate types**: `npm run generate-types` (after route changes)
4. **Build**: `npm run build`

### Troubleshooting Guide

#### Common Issues

1. **"Mode hybrid not detected"**
   - Ensure index.html exists in resources/ or root/
   - Check InertiaConfig is provided in ViteConfig

2. **"InertiaPlugin not found"**
   - Remove InertiaPlugin import
   - Inertia is now integrated in VitePlugin

3. **"Template not found"**
   - Verify root_template="index.html" (not .j2)
   - Check file exists in correct location

4. **"Flash messages not appearing"**
   - Check FlashPlugin is still registered
   - Verify frontend handles flash props

5. **"CSRF validation failed"**
   - Check SPAConfig.inject_csrf=True
   - Verify frontend reads window.__LITESTAR_CSRF__

## Glossary

- **Hybrid Mode**: Inertia.js setup without Jinja2 templates, using HtmlTransformer
- **HtmlTransformer**: Component that injects Inertia page data into static HTML
- **TypeGenConfig**: Configuration for automatic type generation
- **PathConfig**: Configuration for file system paths
- **RuntimeConfig**: Configuration for runtime behavior (dev server, etc.)
- **VitePlugin**: Unified plugin handling Vite and optionally Inertia
- **SPAConfig**: Configuration for SPA HTML transformations
- **routes.ts**: Generated TypeScript file with type-safe route helpers
- **openapi.json**: Generated OpenAPI schema for the API
- **SDK**: Type-safe API client generated from OpenAPI schema

---

## Comparison Matrix

### Before vs After Configuration

| Aspect | Before (Current) | After (Target) |
|--------|------------------|----------------|
| ViteConfig params | 8 flat parameters | 4 nested sub-configs |
| InertiaConfig | Separate module | Nested in ViteConfig |
| Plugins needed | 2 (Vite + Inertia) | 1 (Vite only) |
| Template engine | Jinja2 required | Not required |
| Root template | `.j2` Jinja template | Static `.html` |
| Mode | Implicit | Explicit/auto-detected |
| Type generation | None | Full (routes, SDK) |
| CSRF handling | Manual | Auto-injected |

### Before vs After Plugin Setup

**Before (5 lines)**:
```python
from litestar_vite import VitePlugin
from litestar_vite.inertia import InertiaPlugin

vite = VitePlugin(config=config.vite)
inertia = InertiaPlugin(config=config.inertia)
# Must register both in plugins list
```

**After (3 lines)**:
```python
from app import config

vite = config.vite  # VitePlugin with Inertia integrated
# Single plugin handles everything
```

### Feature Comparison

| Feature | Before | After |
|---------|--------|-------|
| Hot Module Replacement | Yes | Yes |
| React Fast Refresh | Configurable | Configurable |
| Inertia.js Support | Separate plugin | Integrated |
| Template rendering | Jinja2 | HtmlTransformer |
| Route generation | No | Yes (routes.ts) |
| OpenAPI export | Manual | Automatic |
| SDK generation | Manual | Automatic |
| Zod schemas | No | Yes (optional) |
| Static file serving | Manual config | Auto-configured |
| Dev server management | Manual | Auto-managed |

---

## Implementation Estimate

This migration involves:

- **Python files to modify**: 4 core files
- **Python files to delete**: 1 template file
- **Frontend files to create**: 3 new files
- **Frontend files to modify**: 2 existing files
- **Configuration changes**: Significant restructuring
- **Testing requirements**: Full regression testing

The migration should be completed in a single focused session with careful attention to authentication flows and flash message handling.

---

## References

- litestar-vite documentation: https://litestar-vite.litestar.dev/
- Inertia.js documentation: https://inertiajs.com/
- @hey-api/openapi-ts: https://github.com/hey-api/openapi-ts
- litestar-vite examples: `/home/cody/code/litestar/litestar-vite/examples/react-inertia/`
- litestar-fullstack-spa reference: `/home/cody/code/litestar/litestar-fullstack-spa/`

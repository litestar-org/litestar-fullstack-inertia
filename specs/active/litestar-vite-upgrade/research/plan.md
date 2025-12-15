# Litestar-Vite Alpha 6 Upgrade - Research Plan

## Executive Summary

This document outlines the comprehensive research and planning required to upgrade the litestar-fullstack-inertia project to use litestar-vite alpha 6's improved Inertia.js implementation. The upgrade transforms the project from a template-based Inertia setup to a modern hybrid mode with automatic type generation, aligning it with its intended role as a showcase application for Litestar and Inertia.js.

## Research Methodology

### Sources Analyzed

1. **Pattern Library**: `specs/guides/patterns/README.md` - Existing project patterns
2. **Internal Configuration**: `app/config.py`, `app/server/plugins.py`, `app/server/core.py`
3. **Template Reference**: `litestar-vite/examples/react-inertia/` - New implementation pattern
4. **Feature Reference**: `litestar-fullstack-spa/` - Features to adopt
5. **Core Library Source**: `litestar-vite/src/py/litestar_vite/config.py` - New config API

### Key Findings

#### Finding 1: Unified ViteConfig Architecture

The new litestar-vite alpha 6 introduces a fundamentally restructured configuration system. Instead of flat configuration parameters, it uses a nested dataclass architecture:

```
ViteConfig
├── paths: PathConfig
│   ├── root: Path
│   ├── bundle_dir: Path
│   ├── resource_dir: Path
│   ├── public_dir: Path
│   ├── manifest_name: str
│   ├── hot_file: str
│   └── asset_url: str
├── runtime: RuntimeConfig
│   ├── dev_mode: bool
│   ├── proxy_mode: Literal['vite', 'direct', 'proxy'] | None
│   ├── host: str
│   ├── port: int
│   ├── executor: Literal['node', 'bun', 'deno', 'yarn', 'pnpm']
│   ├── is_react: bool
│   ├── ssr_enabled: bool
│   └── spa_handler: bool
├── types: TypeGenConfig | None
│   ├── output: Path
│   ├── openapi_path: Path
│   ├── routes_path: Path
│   ├── routes_ts_path: Path
│   ├── generate_zod: bool
│   ├── generate_sdk: bool
│   └── generate_routes: bool
├── inertia: InertiaConfig | None
│   ├── root_template: str
│   ├── redirect_unauthorized_to: str | None
│   ├── extra_static_page_props: dict
│   ├── extra_session_page_props: set
│   ├── spa_mode: bool (auto-detected)
│   └── app_selector: str
├── spa: SPAConfig | None
│   ├── inject_csrf: bool
│   ├── csrf_var_name: str
│   └── app_selector: str
├── mode: Literal['spa', 'template', 'htmx', 'hybrid', 'ssr', 'ssg', 'external']
├── dev_mode: bool (shortcut)
├── base_url: str | None
└── deploy: DeployConfig | bool
```

This architecture provides:
- Clear separation of concerns
- Type-safe configuration
- Intelligent defaults and auto-detection
- Backward compatibility through convenience properties

#### Finding 2: Mode Auto-Detection

The new ViteConfig has sophisticated mode auto-detection:

1. If Inertia is enabled with `spa_mode=True` -> Hybrid mode
2. If Inertia is enabled and `index.html` exists -> Hybrid mode (auto-detected)
3. If Inertia is enabled without index.html -> Template mode (Jinja-based)
4. If `index.html` exists (no Inertia) -> SPA mode
5. If Jinja2 is installed -> Template mode
6. Default -> SPA mode

For this project, we want **hybrid mode** (Inertia without Jinja templates), which is auto-detected when:
- `inertia=InertiaConfig(...)` is provided
- An `index.html` file exists in resources/, root/, or public/

#### Finding 3: InertiaPlugin Integration

The InertiaPlugin is now automatically registered by VitePlugin when `inertia` config is provided. This means:

**Before (Current):**
```python
# plugins.py
vite = VitePlugin(config=config.vite)
inertia = InertiaPlugin(config=config.inertia)

# core.py - must include both
plugins.extend([plugins.vite, plugins.inertia])
```

**After (Target):**
```python
# plugins.py
vite = VitePlugin(config=config.vite)  # inertia is nested in vite config

# core.py - single plugin
plugins.extend([plugins.vite])  # Inertia is handled internally
```

#### Finding 4: Type Generation System

The new TypeGenConfig enables automatic generation of:

1. **routes.ts** - Typed route helpers (similar to Laravel's Ziggy)
   - Route name -> URL mapping
   - Type-safe parameter handling
   - Export: `route()`, `hasRoute()`, `routes`

2. **routes.json** - Route metadata in JSON format
   - Consumed by routes.ts
   - Contains URI patterns, methods, parameters

3. **openapi.json** - OpenAPI schema
   - Full API documentation
   - Input for SDK generation

4. **API SDK** (via @hey-api/openapi-ts)
   - Type-safe API client
   - Axios-based HTTP calls
   - Automatic type inference

Configuration:
```python
types=TypeGenConfig(
    output=Path("src/lib/generated"),
    generate_zod=True,       # Zod schemas from OpenAPI
    generate_sdk=True,       # SDK generation enabled
    generate_routes=True,    # routes.ts generation
)
```

Frontend configuration (openapi-ts.config.ts):
```typescript
import { defineConfig } from "@hey-api/openapi-ts"

export default defineConfig({
  input: "./src/lib/generated/openapi.json",
  output: "./src/lib/generated/api",
  plugins: ["@hey-api/typescript", "@hey-api/schemas", "@hey-api/sdk", "@hey-api/client-axios"],
})
```

#### Finding 5: Template-less Inertia (Hybrid Mode)

The hybrid mode uses HtmlTransformer instead of Jinja2 templates:

**How it works:**
1. Static `index.html` is read at startup
2. HtmlTransformer injects page data into `data-page` attribute
3. CSRF token injected as `window.__LITESTAR_CSRF__`
4. No Jinja2 rendering overhead

**index.html structure:**
```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title inertia>App Name</title>
  </head>
  <body>
    <div id="app" data-page="{{ page | tojson | e }}"></div>
    <script type="module" src="/resources/main.tsx"></script>
  </body>
</html>
```

Key elements:
- `<title inertia>` - Enables Inertia title management
- `data-page="{{ page | tojson | e }}"` - Page data injection point
- Script path relative to resources directory

#### Finding 6: Features from litestar-fullstack-spa

The litestar-fullstack-spa project provides patterns to adopt:

1. **ViteConfig with types enabled**
```python
vite = ViteConfig(
    mode="spa",
    dev_mode=settings.vite.DEV_MODE,
    paths=PathConfig(
        root=BASE_DIR.parent.parent / "js",
        bundle_dir=settings.vite.BUNDLE_DIR,
        asset_url=settings.vite.ASSET_URL,
    ),
    types=TypeGenConfig(
        output=BASE_DIR.parent.parent / "js" / "src" / "lib" / "generated",
        generate_zod=True,
        generate_sdk=True,
        generate_routes=True,
    ),
)
```

2. **SAQ with PostgreSQL broker**
```python
saq = SAQConfig(
    queue_configs=[
        QueueConfig(
            name="background-tasks",
            dsn=settings.db.URL.replace("postgresql+psycopg", "postgresql"),
            broker_options={
                "stats_table": "task_queue_stats",
                "jobs_table": "task_queue",
                "versions_table": "task_queue_ddl_version",
            },
        )
    ],
)
```

3. **Problem Details Plugin**
```python
from litestar.plugins.problem_details import ProblemDetailsConfig
problem_details = ProblemDetailsConfig(enable_for_all_http_exceptions=True)
```

4. **Cleaner Logging Abstraction**
- Separate log configuration module
- Helper functions for processors

#### Finding 7: Current WebController Analysis

The current WebController (`app/domain/web/controllers.py`) has:

| Route | Path | Purpose | Keep? |
|-------|------|---------|-------|
| home | `/` | Redirect to dashboard or landing | Yes (modify) |
| landing | `/landing/` | Marketing landing page | Yes |
| dashboard | `/dashboard/` | User dashboard | Yes |
| about | `/about/` | About page | Evaluate |
| privacy-policy | `/privacy-policy/` | Privacy policy | Yes |
| terms-of-service | `/terms-of-service/` | Terms of service | Yes |
| favicon | `/favicon.ico` | Serve favicon | Evaluate |

The favicon route may be handled by static file serving in the new setup.

#### Finding 8: Frontend Dependencies Update

Current package.json dependencies requiring update:

```json
{
  "dependencies": {
    // Keep most existing dependencies
  },
  "devDependencies": {
    "litestar-vite-plugin": "^0.10.0",  // Update to latest
    // Add:
    "@hey-api/openapi-ts": "^0.88.0",
    "@tailwindcss/vite": "^4.1.17",  // For Tailwind 4 (optional)
    "zod": "^4.0.0"  // For Zod schema generation
  }
}
```

New scripts:
```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build && tsc -b --noEmit",
    "preview": "vite preview",
    "generate-types": "openapi-ts --config openapi-ts.config.ts"
  }
}
```

## Technical Specifications

### Python Package Requirements

```toml
[project.dependencies]
litestar-vite = ">=0.7.0a6"  # Or latest alpha
```

### Configuration Migration Map

| Old Config | New Config Location |
|------------|---------------------|
| `bundle_dir` | `paths.bundle_dir` |
| `resource_dir` | `paths.resource_dir` |
| `use_server_lifespan` | Auto-managed |
| `dev_mode` | `runtime.dev_mode` or top-level shortcut |
| `hot_reload` | Derived from `runtime.dev_mode` |
| `is_react` | `runtime.is_react` |
| `port` | `runtime.port` |
| `host` | `runtime.host` |

### InertiaConfig Migration Map

| Old Config | New Config Location |
|------------|---------------------|
| Separate InertiaConfig | Nested in `vite.inertia` |
| `root_template` | `inertia.root_template` (now points to HTML) |
| `redirect_unauthorized_to` | `inertia.redirect_unauthorized_to` |
| `extra_static_page_props` | `inertia.extra_static_page_props` |
| `extra_session_page_props` | `inertia.extra_session_page_props` |

## Implementation Recommendations

### Phase 1: Backend Configuration
1. Update pyproject.toml dependency
2. Restructure app/config.py with new ViteConfig
3. Simplify app/server/plugins.py
4. Update app/server/core.py plugin list

### Phase 2: Template Migration
1. Create resources/index.html
2. Remove Jinja templates
3. Verify mode auto-detection

### Phase 3: Frontend Restructuring
1. Create src/lib/generated/ folder
2. Update vite.config.ts
3. Add openapi-ts.config.ts
4. Update package.json

### Phase 4: Type Generation
1. Test route generation
2. Configure SDK generation
3. Integrate generated types

### Phase 5: Cleanup
1. Remove WebController if not needed
2. Clean up unused templates
3. Remove deprecated settings

### Phase 6: Testing
1. Run full test suite
2. Manual testing of all pages
3. Verify authentication flows

## Detailed Configuration Examples

### Complete ViteConfig for This Project

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
        # Mode will be auto-detected as "hybrid" due to Inertia + index.html
        dev_mode=settings.vite.DEV_MODE,

        # Path configuration
        paths=PathConfig(
            root=BASE_DIR.parent,  # Project root containing resources/
            resource_dir=Path("resources"),
            bundle_dir=Path("public"),  # Or existing path
            asset_url=settings.vite.ASSET_URL,
        ),

        # Runtime configuration
        runtime=RuntimeConfig(
            host=settings.vite.HOST,
            port=settings.vite.PORT,
            is_react=True,  # Enable React Fast Refresh
            executor="npm",  # or "bun", "pnpm", "yarn"
        ),

        # Inertia configuration (presence enables Inertia)
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

        # Type generation configuration
        types=TypeGenConfig(
            output=BASE_DIR.parent / "src" / "lib" / "generated",
            generate_zod=True,
            generate_sdk=True,
            generate_routes=True,
        ),
    )
)
```

### Updated ViteSettings Dataclass

```python
@dataclass
class ViteSettings:
    """Server configurations."""

    DEV_MODE: bool = field(
        default_factory=lambda: os.getenv("VITE_DEV_MODE", "False") in TRUE_VALUES,
    )
    """Enable development mode with HMR."""

    HOST: str = field(default_factory=lambda: os.getenv("VITE_HOST", "127.0.0.1"))
    """The host the vite process will listen on."""

    PORT: int = field(default_factory=lambda: int(os.getenv("VITE_PORT", "5173")))
    """The port to start vite on."""

    ASSET_URL: str = field(default_factory=lambda: os.getenv("ASSET_URL", "/static/"))
    """Base URL for assets."""

    # Removed: HOT_RELOAD (derived from DEV_MODE)
    # Removed: USE_SERVER_LIFESPAN (auto-managed)
    # Removed: ENABLE_REACT_HELPERS (now is_react in RuntimeConfig)
    # Removed: BUNDLE_DIR, RESOURCE_DIR, TEMPLATE_DIR (moved to code)
```

### Updated plugins.py

```python
from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from litestar.plugins.flash import FlashConfig, FlashPlugin
from litestar.plugins.structlog import StructlogPlugin
from litestar_granian import GranianPlugin
from litestar_saq import SAQPlugin
from litestar_vite import VitePlugin

from app import config
from app.server.core import ApplicationCore

structlog = StructlogPlugin(config=config.log)
vite = config.vite  # VitePlugin is now created in config.py
saq = SAQPlugin(config=config.saq)
alchemy = SQLAlchemyPlugin(config=config.alchemy)
granian = GranianPlugin()
app_core = ApplicationCore()
flasher = FlashPlugin(config=FlashConfig())  # May need adjustment
# Removed: inertia = InertiaPlugin(...) - now integrated in VitePlugin
```

### Frontend vite.config.ts

```typescript
import tailwindcss from "@tailwindcss/vite"
import react from "@vitejs/plugin-react"
import litestar from "litestar-vite-plugin"
import { defineConfig } from "vite"

export default defineConfig({
  plugins: [
    tailwindcss(),  // Tailwind 4 style
    react(),
    litestar({
      input: ["resources/main.tsx"],
      // Additional options are now server-side configured
    }),
  ],
  resolve: {
    alias: {
      "@": "/resources",
    },
  },
})
```

## Migration Checklist

### Pre-Migration

- [ ] Create feature branch
- [ ] Document current functionality
- [ ] Ensure all tests pass
- [ ] Backup current configuration

### Backend Migration

- [ ] Update pyproject.toml with litestar-vite alpha 6
- [ ] Run `uv sync` to update dependencies
- [ ] Restructure app/config.py
  - [ ] Import new config classes
  - [ ] Create VitePlugin with nested config
  - [ ] Remove separate InertiaConfig
  - [ ] Remove TemplateConfig for Inertia
- [ ] Update app/server/plugins.py
  - [ ] Remove InertiaPlugin import
  - [ ] Reference vite from config
- [ ] Update app/server/core.py
  - [ ] Remove plugins.inertia from list
  - [ ] Verify plugin order
- [ ] Update app/lib/settings.py
  - [ ] Simplify ViteSettings

### Template Migration

- [ ] Create resources/index.html
- [ ] Verify data-page attribute syntax
- [ ] Test with dev server
- [ ] Remove app/domain/web/templates/site/index.html.j2

### Frontend Migration

- [ ] Create src/lib/generated/ directory
- [ ] Update package.json
  - [ ] Update litestar-vite-plugin
  - [ ] Add @hey-api/openapi-ts
  - [ ] Add generate-types script
- [ ] Create openapi-ts.config.ts
- [ ] Update vite.config.ts
- [ ] Run npm install

### Testing

- [ ] Run `make test`
- [ ] Run `make lint`
- [ ] Run `npx biome check resources/`
- [ ] Test login flow
- [ ] Test registration flow
- [ ] Test OAuth flows
- [ ] Test dashboard access
- [ ] Test flash messages
- [ ] Verify type generation

### Cleanup

- [ ] Remove unused templates
- [ ] Remove deprecated settings
- [ ] Update documentation
- [ ] Clean up comments

## Risk Mitigation Strategies

### Authentication Flow Protection

The authentication flow is critical and uses session-based auth with Inertia redirects:

```python
@post(component="auth/login", name="login.check", path="/login/")
async def login(self, request, data, users_service):
    user = await users_service.authenticate(data.username, data.password)
    request.set_session({"user_id": user.email})
    return InertiaRedirect(request, request.url_for("dashboard"))
```

To protect this during migration:

1. **Incremental Testing**: Test login after each config change
2. **Session Compatibility**: Verify session handling works with hybrid mode
3. **Redirect Verification**: Ensure InertiaRedirect works without Jinja templates

### Flash Message Handling

Flash messages currently use the FlashPlugin with Jinja templates:

```python
flash(request, "Your account was successfully authenticated.", category="info")
```

In hybrid mode, flash messages need to be handled differently:
- Use Inertia's shared data mechanism
- Or inject via SPAConfig's CSRF injection

### Static File Serving

The new VitePlugin auto-configures static file serving. Verify:
- Favicon is served correctly
- CSS/JS bundles load
- Public assets accessible

## Performance Considerations

### Build Time Improvements

The new type generation runs at build time, not runtime:
- OpenAPI schema extracted once
- Routes generated statically
- SDK types compiled at build

### Runtime Improvements

- No Jinja template compilation for Inertia pages
- HtmlTransformer is simpler than Jinja2
- Static file serving optimized

### Development Experience

- Hot reload works out of the box
- Type-safe route helpers
- SDK provides IntelliSense for API calls

## Future Enhancements

After completing the migration, consider:

1. **Full Tailwind 4 Migration**: Update from Tailwind 3 to 4 with @tailwindcss/vite
2. **Zod Validation**: Use generated Zod schemas for frontend validation
3. **TanStack Query Integration**: Like litestar-fullstack-spa
4. **PostgreSQL SAQ Broker**: For more reliable task queues
5. **Problem Details Plugin**: For standardized error responses

## Conclusion

This research establishes a clear path for upgrading the litestar-fullstack-inertia project to litestar-vite alpha 6. The upgrade will:

1. Simplify the architecture (1 plugin instead of 2)
2. Enable modern type generation (routes.ts, SDK)
3. Remove Jinja template dependency for Inertia
4. Align with showcase application standards
5. Improve developer experience with typed routes and API client

The implementation should proceed in phases to minimize risk and allow for incremental testing. The detailed configuration examples and migration checklist provide a concrete roadmap for the implementation phase.

# Litestar-Vite Alpha 6 Upgrade Analysis

## Intelligence Context

- **Complexity**: Complex (10+ checkpoints required)
- **Similar Features Analyzed**: react-inertia template, litestar-fullstack-spa
- **Patterns to Follow**: Unified ViteConfig, PathConfig/RuntimeConfig/TypeGenConfig structure
- **Tool Used for Analysis**: mcp__pal__planner (3-step structured planning)

## Problem Statement

The litestar-fullstack-inertia project needs to be upgraded to serve as a showcase application for Litestar and Inertia.js integration. The latest release of litestar-vite alpha 6 introduces a significantly improved implementation with:

1. **Unified Configuration**: Single ViteConfig with nested sub-configs
2. **Hybrid Mode**: Template-less Inertia using HtmlTransformer
3. **Type Generation**: Built-in routes.ts, OpenAPI schema, and SDK generation
4. **Simplified Plugin Architecture**: InertiaPlugin integrated into VitePlugin

## Current State Analysis

### Current Configuration Pattern (app/config.py)

```python
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

### Current Plugin Pattern (app/server/plugins.py)

```python
from litestar_vite import VitePlugin
from litestar_vite.inertia import InertiaPlugin

vite = VitePlugin(config=config.vite)
inertia = InertiaPlugin(config=config.inertia)
```

### Issues with Current Implementation

1. **Separate Inertia Plugin**: Creates unnecessary complexity
2. **Jinja Template Dependency**: Uses `site/index.html.j2` for Inertia root
3. **No Type Generation**: Routes and OpenAPI schema not auto-generated
4. **Outdated ViteConfig API**: Missing new PathConfig, RuntimeConfig, TypeGenConfig
5. **WebController for Static Pages**: Contains routes that may not be needed

## Target State (from react-inertia template)

### New Configuration Pattern

```python
from litestar_vite import VitePlugin, ViteConfig, PathConfig, RuntimeConfig, TypeGenConfig, InertiaConfig

vite = VitePlugin(
    config=ViteConfig(
        dev_mode=DEV_MODE,
        paths=PathConfig(
            root=BASE_DIR,
            resource_dir="resources",
            bundle_dir=Path("public"),
        ),
        runtime=RuntimeConfig(
            port=5173,
            host="127.0.0.1",
        ),
        inertia=InertiaConfig(
            root_template="index.html",  # Plain HTML, not Jinja
            redirect_unauthorized_to="/login",
        ),
        types=TypeGenConfig(
            output=Path("src/lib/generated"),
            generate_zod=True,
            generate_sdk=True,
            generate_routes=True,
        ),
    )
)
```

### Key Differences

| Aspect | Current | Target |
|--------|---------|--------|
| Plugin Count | 2 (VitePlugin + InertiaPlugin) | 1 (VitePlugin only) |
| Template | Jinja (`site/index.html.j2`) | Plain HTML (`index.html`) |
| Mode | Template-based | Hybrid (HtmlTransformer) |
| Type Generation | None | routes.ts, openapi.json, SDK |
| Config Structure | Flat | Nested (Path/Runtime/Type/Inertia) |

## Files Requiring Modification

### Backend (Python)

1. **app/config.py** - Major restructuring
   - Import new config classes
   - Restructure ViteConfig with sub-configs
   - Remove separate InertiaConfig at module level
   - Remove TemplateConfig for Inertia

2. **app/server/plugins.py** - Simplification
   - Remove InertiaPlugin import and instance
   - Update VitePlugin usage

3. **app/server/core.py** - Plugin list update
   - Remove `plugins.inertia` from list
   - Remove `plugins.flasher` (may not work with hybrid mode)
   - Remove `config.templates` if no longer needed

4. **app/lib/settings.py** - ViteSettings update
   - Align with new PathConfig/RuntimeConfig patterns
   - Remove deprecated settings

5. **app/domain/web/controllers.py** - Evaluate and clean
   - Determine which routes are still needed
   - Remove template-dependent logic

6. **app/domain/web/templates/** - Remove
   - Delete Jinja templates for Inertia

### Frontend (TypeScript/React)

1. **Create resources/index.html** - Inertia root
   ```html
   <!DOCTYPE html>
   <html lang="en">
     <head>
       <meta charset="UTF-8" />
       <meta name="viewport" content="width=device-width, initial-scale=1.0" />
       <title inertia>Litestar Fullstack</title>
     </head>
     <body>
       <div id="app" data-page="{{ page | tojson | e }}"></div>
       <script type="module" src="/resources/main.tsx"></script>
     </body>
   </html>
   ```

2. **Create src/lib/generated/** - Type generation output

3. **vite.config.ts** - Update plugin config
   - Consider Tailwind 4 with @tailwindcss/vite

4. **package.json** - Dependencies
   - Update litestar-vite-plugin
   - Add @hey-api/openapi-ts
   - Add generate-types script

5. **Create openapi-ts.config.ts** - SDK config

## Features to Adopt from litestar-fullstack-spa

1. **TypeGenConfig Pattern**
   ```python
   types=TypeGenConfig(
       output=BASE_DIR.parent.parent / "js" / "src" / "lib" / "generated",
       generate_zod=True,
       generate_sdk=True,
       generate_routes=True,
   ),
   ```

2. **Cleaner Logging Configuration** - Already well-structured

3. **SAQ Queue Configuration** - Consider PostgreSQL broker option

4. **Problem Details Plugin** - For better error responses

## Risk Assessment

### High Risk Items
- Authentication flow breaking during template migration
- Session handling changes in hybrid mode
- Static file serving configuration changes

### Medium Risk Items
- Flash messages in hybrid mode
- OAuth callbacks routing
- CSRF token injection

### Mitigation Strategies
- Implement changes incrementally per phase
- Test authentication after each change
- Keep git history clean for easy rollback

## Comparison with react-inertia Template

The `react-inertia` template in litestar-vite examples shows the minimal setup:

```python
vite = VitePlugin(
    config=ViteConfig(
        dev_mode=DEV_MODE,
        paths=PathConfig(root=here, resource_dir="resources"),
        inertia=InertiaConfig(root_template="index.html"),
        types=TypeGenConfig(output=Path("resources/generated"), generate_zod=True),
        runtime=RuntimeConfig(port=5002),
    )
)

app = Litestar(
    route_handlers=[LibraryController],
    plugins=[vite],  # Single plugin
    middleware=[session_backend.middleware],
    debug=True,
)
```

Key observations:
1. Single plugin handles everything
2. `index.html` in root (not resources/) per template
3. Mode is auto-detected as "hybrid" from Inertia + index.html presence
4. TypeGenConfig outputs to resources/generated/

## Recommended Generated Files Location

Per user request: `<root>/src/lib/generated`

This aligns with frontend conventions and separates generated code from manually written code.

## Conclusion

This upgrade is a significant architectural change that will:
1. Simplify the plugin architecture
2. Enable modern type generation
3. Remove Jinja template dependency for Inertia
4. Align with the latest litestar-vite patterns

The implementation requires careful phasing to avoid breaking changes, with particular attention to authentication and session handling.

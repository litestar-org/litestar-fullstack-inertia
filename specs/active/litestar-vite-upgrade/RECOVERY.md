# Recovery Guide for Litestar-Vite Alpha 6 Upgrade

## Intelligence Context (for session resumption)

- **Complexity**: Complex (10+ checkpoints)
- **Patterns Identified**:
  - Unified ViteConfig with nested sub-configs
  - Hybrid mode for template-less Inertia
  - TypeGenConfig for automatic type generation
  - Single VitePlugin handles all functionality
- **Similar Features Analyzed**:
  - `litestar-vite/examples/react-inertia/`
  - `litestar-fullstack-spa/`

## Current Status

- [x] PRD complete (3366 words)
- [x] Tasks defined (32 tasks across 7 phases)
- [x] Research complete (2269 words)
- [ ] Ready for implementation

## Key Files

| Document | Path | Description |
|----------|------|-------------|
| PRD | `specs/active/litestar-vite-upgrade/prd.md` | Full product requirements |
| Tasks | `specs/active/litestar-vite-upgrade/tasks.md` | Implementation task breakdown |
| Research Analysis | `specs/active/litestar-vite-upgrade/research/analysis.md` | Technical analysis |
| Research Plan | `specs/active/litestar-vite-upgrade/research/plan.md` | Detailed research findings |
| This file | `specs/active/litestar-vite-upgrade/RECOVERY.md` | Session resumption guide |

## Reference Files (External)

| File | Path | Purpose |
|------|------|---------|
| react-inertia template | `/home/cody/code/litestar/litestar-vite/examples/react-inertia/` | New pattern reference |
| litestar-fullstack-spa | `/home/cody/code/litestar/litestar-fullstack-spa/` | Feature reference |
| litestar-vite config | `/home/cody/code/litestar/litestar-vite/src/py/litestar_vite/config.py` | New config API source |

## To Resume

1. Read this file for context
2. Read PRD for full requirements
3. Check task completion status in tasks.md
4. Run `/implement litestar-vite-upgrade` to continue implementation

## Quick Context Summary

This upgrade transforms the litestar-fullstack-inertia project from:

**OLD ARCHITECTURE**:
- Separate VitePlugin + InertiaPlugin
- Jinja2 templates for Inertia root
- No type generation
- Flat ViteConfig parameters

**NEW ARCHITECTURE**:
- Single VitePlugin with nested configs
- Hybrid mode with HtmlTransformer (no Jinja)
- Automatic type generation (routes.ts, SDK)
- Structured sub-configs (PathConfig, RuntimeConfig, etc.)

## Key Configuration Changes

### Before (app/config.py)

```python
from litestar_vite import ViteConfig
from litestar_vite.inertia import InertiaConfig

vite = ViteConfig(bundle_dir=..., resource_dir=..., ...)
inertia = InertiaConfig(root_template="site/index.html.j2", ...)
templates = TemplateConfig(engine=JinjaTemplateEngine(...))
```

### After (app/config.py)

```python
from litestar_vite import VitePlugin, ViteConfig, PathConfig, RuntimeConfig, TypeGenConfig, InertiaConfig

vite = VitePlugin(
    config=ViteConfig(
        dev_mode=...,
        paths=PathConfig(...),
        runtime=RuntimeConfig(...),
        inertia=InertiaConfig(root_template="index.html", ...),
        types=TypeGenConfig(output=Path("src/lib/generated"), ...),
    )
)
```

## Critical Paths to Test

1. **Authentication**: Login, logout, register, OAuth
2. **Session handling**: Session persistence across requests
3. **Flash messages**: Display in hybrid mode
4. **Inertia navigation**: Client-side routing
5. **Type generation**: routes.ts, openapi.json output

## Rollback Plan

If issues arise during implementation:

1. Git revert configuration changes
2. Restore Jinja template if deleted
3. Revert package.json changes
4. Run `npm install` and `uv sync`

## Phase Completion Checklist

- [ ] Phase 1: Backend Configuration
  - [ ] 1.1: Update dependencies
  - [ ] 1.2: Restructure config.py
  - [ ] 1.3: Update plugins.py
  - [ ] 1.4: Update core.py
  - [ ] 1.5: Simplify settings.py

- [ ] Phase 2: Template Migration
  - [ ] 2.1: Create index.html
  - [ ] 2.2: Verify mode detection
  - [ ] 2.3: Remove Jinja template

- [ ] Phase 3: WebController Cleanup
  - [ ] 3.1: Evaluate routes
  - [ ] 3.2: Test favicon
  - [ ] 3.3: Update registration

- [ ] Phase 4: Frontend Restructuring
  - [ ] 4.1: Create generated/ directory
  - [ ] 4.2: Update package.json
  - [ ] 4.3: Create openapi-ts.config.ts
  - [ ] 4.4: Update vite.config.ts
  - [ ] 4.5: Update main.tsx

- [ ] Phase 5: Type Generation
  - [ ] 5.1: Verify TypeGenConfig
  - [ ] 5.2: Generate types
  - [ ] 5.3: Generate SDK
  - [ ] 5.4: Test types

- [ ] Phase 6: Testing
  - [ ] 6.1: Backend tests
  - [ ] 6.2: Backend linting
  - [ ] 6.3: Frontend linting
  - [ ] 6.4: Auth testing
  - [ ] 6.5: Page testing
  - [ ] 6.6: Flash messages
  - [ ] 6.7: HMR testing

- [ ] Phase 7: Documentation
  - [ ] 7.1: Update CLAUDE.md
  - [ ] 7.2: Update README
  - [ ] 7.3: Update patterns

## Contact Points

- litestar-vite issues: https://github.com/litestar-org/litestar-vite/issues
- Litestar Discord: https://discord.gg/litestar

## Generated on

2025-12-06

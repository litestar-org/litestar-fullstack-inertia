# Implementation Tasks

## Overview

This task breakdown follows the phased implementation strategy from the PRD. Tasks are organized by phase with clear dependencies and success criteria.

---

## Phase 1: Backend Configuration (Priority: Critical)

### Task 1.1: Update Python Dependencies

- [ ] Update pyproject.toml to require litestar-vite alpha 6+
- [ ] Run `uv sync` to update dependencies
- [ ] Verify litestar-vite version installed

**Success Criteria**: `uv pip show litestar-vite` shows version >= 0.7.0a6

### Task 1.2: Restructure app/config.py

- [ ] Add new imports:
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
  ```
- [ ] Remove old imports:
  - Remove `from litestar_vite import ViteConfig`
  - Remove `from litestar_vite.inertia import InertiaConfig`
  - Remove `from litestar.contrib.jinja import JinjaTemplateEngine`
  - Remove `from litestar.template import TemplateConfig` (if only for Inertia)
- [ ] Create new VitePlugin configuration with nested configs
- [ ] Remove old `vite = ViteConfig(...)` assignment
- [ ] Remove old `inertia = InertiaConfig(...)` assignment
- [ ] Remove `templates = TemplateConfig(...)` (if only for Inertia)

**Success Criteria**: config.py compiles without errors, imports new classes

### Task 1.3: Update app/server/plugins.py

- [ ] Remove `from litestar_vite import VitePlugin` (moved to config)
- [ ] Remove `from litestar_vite.inertia import InertiaPlugin`
- [ ] Update vite assignment: `vite = config.vite`
- [ ] Remove `inertia = InertiaPlugin(config=config.inertia)`

**Success Criteria**: plugins.py compiles, no InertiaPlugin reference

### Task 1.4: Update app/server/core.py

- [ ] Remove `plugins.inertia` from plugin list
- [ ] Verify `plugins.vite` is in plugin list
- [ ] Remove `config.templates` assignment if not needed elsewhere
- [ ] Verify plugin order (vite should come before others that might depend on it)

**Success Criteria**: core.py compiles, application starts without plugin errors

### Task 1.5: Simplify app/lib/settings.py

- [ ] Remove deprecated ViteSettings fields:
  - Remove `HOT_RELOAD`
  - Remove `USE_SERVER_LIFESPAN`
  - Remove `ENABLE_REACT_HELPERS`
  - Remove `BUNDLE_DIR`
  - Remove `RESOURCE_DIR`
  - Remove `TEMPLATE_DIR`
- [ ] Keep essential fields:
  - `DEV_MODE`
  - `HOST`
  - `PORT`
  - `ASSET_URL`

**Success Criteria**: settings.py compiles, only essential vite settings remain

---

## Phase 2: Template Migration (Priority: High)

### Task 2.1: Create resources/index.html

- [ ] Create new file: `resources/index.html`
- [ ] Add HTML structure with Inertia elements:
  - `<title inertia>` tag
  - `<div id="app" data-page="{{ page | tojson | e }}">`
  - Script src pointing to main.tsx
- [ ] Verify favicon link

**Success Criteria**: index.html exists with correct structure

### Task 2.2: Verify Mode Auto-Detection

- [ ] Start application in dev mode
- [ ] Verify mode is detected as "hybrid"
- [ ] Check console/logs for mode detection messages

**Success Criteria**: Application logs show "hybrid" mode

### Task 2.3: Remove Jinja Template

- [ ] Delete `app/domain/web/templates/site/index.html.j2`
- [ ] Verify application still starts
- [ ] Test a page renders correctly

**Success Criteria**: Template deleted, pages still render

---

## Phase 3: WebController Cleanup (Priority: Medium)

### Task 3.1: Evaluate WebController Routes

- [ ] Review each route in `app/domain/web/controllers.py`
- [ ] Document decision for each:
  - `home` (`/`): Keep (redirect logic)
  - `landing` (`/landing/`): Keep
  - `dashboard` (`/dashboard/`): Keep
  - `about` (`/about/`): Evaluate - keep or remove
  - `privacy-policy` (`/privacy-policy/`): Keep
  - `terms-of-service` (`/terms-of-service/`): Keep
  - `favicon` (`/favicon.ico`): Test if auto-served, remove if redundant

### Task 3.2: Test Favicon Handling

- [ ] Access `/favicon.ico` endpoint
- [ ] Check if VitePlugin serves it automatically
- [ ] If auto-served, remove favicon route from controller

**Success Criteria**: Favicon accessible, redundant route removed if applicable

### Task 3.3: Update Route Registration (if needed)

- [ ] If WebController is modified, verify core.py still registers it correctly
- [ ] Run tests to ensure routes still work

**Success Criteria**: All kept routes function correctly

---

## Phase 4: Frontend Restructuring (Priority: High)

### Task 4.1: Create Generated Types Directory

- [ ] Create directory: `src/lib/generated/`
- [ ] Create `.gitkeep` file (for empty directory tracking)

**Success Criteria**: Directory exists

### Task 4.2: Update package.json

- [ ] Update `litestar-vite-plugin` to latest version
- [ ] Add `@hey-api/openapi-ts` to devDependencies
- [ ] Add `zod` to dependencies (if using Zod generation)
- [ ] Add `generate-types` script:
  ```json
  "generate-types": "openapi-ts --config openapi-ts.config.ts"
  ```
- [ ] Run `npm install`

**Success Criteria**: npm install succeeds, new packages listed

### Task 4.3: Create openapi-ts.config.ts

- [ ] Create configuration file for SDK generation
- [ ] Configure input path: `./src/lib/generated/openapi.json`
- [ ] Configure output path: `./src/lib/generated/api`
- [ ] Add plugins: typescript, schemas, sdk, client-axios

**Success Criteria**: Config file exists with correct paths

### Task 4.4: Update vite.config.ts

- [ ] Review current configuration
- [ ] Update litestar plugin options if needed
- [ ] Consider adding `@tailwindcss/vite` (optional, for Tailwind 4)
- [ ] Verify resolve aliases

**Success Criteria**: Vite config updated, dev server starts

### Task 4.5: Update resources/main.tsx (if needed)

- [ ] Verify main.tsx works with new setup
- [ ] Update imports if paths changed
- [ ] Ensure ThemeProvider still works

**Success Criteria**: Frontend renders without errors

---

## Phase 5: Type Generation Setup (Priority: Medium)

### Task 5.1: Verify TypeGenConfig in Python

- [ ] Confirm TypeGenConfig is set in ViteConfig
- [ ] Verify output path is `src/lib/generated`
- [ ] Check generate_zod, generate_sdk, generate_routes flags

**Success Criteria**: TypeGenConfig correctly configured

### Task 5.2: Generate Types

- [ ] Start application to trigger type generation
- [ ] Verify `src/lib/generated/routes.json` exists
- [ ] Verify `src/lib/generated/routes.ts` exists
- [ ] Verify `src/lib/generated/openapi.json` exists

**Success Criteria**: All generated files exist

### Task 5.3: Generate SDK

- [ ] Run `npm run generate-types`
- [ ] Verify `src/lib/generated/api/` directory created
- [ ] Check for TypeScript definition files

**Success Criteria**: SDK generated without errors

### Task 5.4: Test Generated Types

- [ ] Import route helper in a component
- [ ] Verify TypeScript accepts the import
- [ ] Test a route() call compiles

**Success Criteria**: Generated types usable in frontend

---

## Phase 6: Testing & Validation (Priority: Critical)

### Task 6.1: Run Backend Tests

- [ ] Run `make test`
- [ ] Fix any failing tests
- [ ] Ensure 90%+ coverage on modified modules

**Success Criteria**: All tests pass

### Task 6.2: Run Linting

- [ ] Run `make lint` (includes pre-commit + type-check)
- [ ] Fix any linting errors
- [ ] Verify mypy passes
- [ ] Verify pyright passes

**Success Criteria**: All lint checks pass

### Task 6.3: Run Frontend Linting

- [ ] Run `npx biome check resources/`
- [ ] Fix any Biome errors

**Success Criteria**: Biome check passes

### Task 6.4: Manual Testing - Authentication

- [ ] Test login with username/password
- [ ] Test logout
- [ ] Test registration
- [ ] Test GitHub OAuth login
- [ ] Test Google OAuth login

**Success Criteria**: All auth flows work

### Task 6.5: Manual Testing - Pages

- [ ] Test landing page loads
- [ ] Test dashboard loads (authenticated)
- [ ] Test profile page loads
- [ ] Test profile edit works
- [ ] Test privacy policy page loads
- [ ] Test terms of service page loads

**Success Criteria**: All pages render correctly

### Task 6.6: Manual Testing - Flash Messages

- [ ] Trigger a flash message (e.g., login success)
- [ ] Verify message appears in UI

**Success Criteria**: Flash messages display

### Task 6.7: Manual Testing - HMR

- [ ] Start dev server
- [ ] Modify a React component
- [ ] Verify HMR updates without full reload

**Success Criteria**: HMR works

---

## Phase 7: Documentation (Priority: Low)

### Task 7.1: Update CLAUDE.md

- [ ] Update configuration examples
- [ ] Update plugin references
- [ ] Document type generation

### Task 7.2: Update README (if exists)

- [ ] Update setup instructions if changed
- [ ] Document type generation script

### Task 7.3: Update Pattern Library

- [ ] Document new ViteConfig pattern in `specs/guides/patterns/`
- [ ] Add TypeGenConfig pattern

---

## Task Dependencies

```
1.1 ──> 1.2 ──> 1.3 ──> 1.4 ──> 1.5
                  │
                  v
         2.1 ──> 2.2 ──> 2.3
                          │
                          v
                  3.1 ──> 3.2 ──> 3.3
                                   │
                                   v
         4.1 ──> 4.2 ──> 4.3 ──> 4.4 ──> 4.5
                                          │
                                          v
                  5.1 ──> 5.2 ──> 5.3 ──> 5.4
                                          │
                                          v
         6.1 ──> 6.2 ──> 6.3 ──> 6.4 ──> 6.5 ──> 6.6 ──> 6.7
                                                          │
                                                          v
                                  7.1 ──> 7.2 ──> 7.3
```

---

## Total Tasks: 32

- Phase 1 (Backend Configuration): 5 tasks
- Phase 2 (Template Migration): 3 tasks
- Phase 3 (WebController Cleanup): 3 tasks
- Phase 4 (Frontend Restructuring): 5 tasks
- Phase 5 (Type Generation Setup): 4 tasks
- Phase 6 (Testing & Validation): 7 tasks
- Phase 7 (Documentation): 3 tasks + 2 cleanup tasks in pattern library

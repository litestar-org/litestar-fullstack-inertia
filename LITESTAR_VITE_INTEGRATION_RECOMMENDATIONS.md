# Litestar-Vite Integration Recommendations

**For:** litestar-fullstack-inertia team
**From:** litestar-vite maintainers
**Date:** 2025-12-16
**litestar-vite Version:** 0.15.0+

---

## Executive Summary

After reviewing the `litestar-fullstack-inertia` codebase, we've identified several opportunities to better leverage `litestar-vite` features. This document outlines actionable improvements organized by priority.

---

## Critical Issues

### 1. Missing Route Helpers in Generated Code (BREAKING)

**File:** `resources/layouts/partials/navbar.tsx:26-33`

```tsx
// CURRENT (BROKEN) - isCurrentRoute is used but not defined!
<NavLink active={isCurrentRoute("dashboard")} href={route("home")}>
<NavLink active={isCurrentRoute("teams.*")} href={route("teams.list")}>
<NavLink active={isCurrentRoute("about")} href={route("about")}>
```

**Problem:** `isCurrentRoute` is called but never imported or defined. The generated `routes.ts` is missing the route helper functions (`toRoute`, `currentRoute`, `isRoute`, `isCurrentRoute`).

**Solution:** Regenerate routes with latest `litestar-vite`:

```bash
# Ensure you have litestar-vite >= 0.15.0
uv add litestar-vite@latest

# Regenerate routes
litestar assets generate-types
```

**After regeneration, update navbar.tsx:**

```tsx
import { route, isCurrentRoute } from "@/lib/generated/routes"

// Now works - isCurrentRoute is exported from generated routes
<NavLink active={isCurrentRoute("dashboard")} href={route("home")}>
<NavLink active={isCurrentRoute("teams.*")} href={route("teams.list")}>
```

### 2. Python `from __future__ import annotations` Anti-Pattern

**Impact:** 53 files in `/app/` use this pattern which is explicitly forbidden in litestar-vite guidelines.

**Why it's problematic:**
- Causes runtime issues with Litestar's dependency injection
- Breaks signature parsing for route handlers
- Creates subtle type resolution bugs

**Files requiring changes:** All Python files in `app/` directory.

**Fix:** Remove the import and use explicit string annotations where needed:

```python
# BEFORE (problematic)
from __future__ import annotations

def handler(user: User) -> Response:
    ...

# AFTER (correct)
def handler(user: "User") -> Response:
    ...

# Or use TYPE_CHECKING for type-only imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.db.models import User
```

---

## High Priority Improvements

### 3. Type-Safe Page Props

**Current State:** Manual interface definitions in each page component.

**File:** `resources/pages/team/show.tsx:10-37`

```tsx
// CURRENT - Manual interface definitions
interface TeamMember {
  id: string
  userId: string
  name: string | null
  // ...
}

interface Props {
  team: Team
  members: TeamMember[]
  permissions: Permissions
}

export default function TeamShow({ team, members, permissions }: Props) {
```

**Solution:** Use generated page props from `page-props.ts`:

```tsx
// IMPROVED - Import from generated types
import type { PagePropsFor } from "@/lib/generated/page-props"

// Type is automatically inferred from backend
export default function TeamShow(props: PagePropsFor<"team/show">) {
  const { team, members, permissions } = props
```

**Backend requirement:** Ensure your controller returns a typed schema:

```python
# In teams/controllers.py
from app.domain.teams.schemas import TeamShowResponse

@get(component="team/show")
async def get_team(self, ...) -> TeamShowResponse:
    return TeamShowResponse(
        team=team_data,
        members=members_list,
        permissions=permissions_dict
    )
```

### 4. Flash Message Auto-Display

**Current State:** Manual flash handling in forms.

**File:** `resources/pages/auth/partials/user-login-form.tsx:68-74`

```tsx
// CURRENT - Manual flash checking
{flash?.error && (
  <Alert variant="destructive">
    <AlertDescription>{flash.error.join("\n")}</AlertDescription>
  </Alert>
)}
```

**Solution:** Create a reusable flash message hook/component:

```tsx
// resources/hooks/useFlash.ts
import { usePage } from "@inertiajs/react"
import { useEffect } from "react"
import { toast } from "sonner"

export function useFlashMessages() {
  const { flash } = usePage<InertiaProps>().props

  useEffect(() => {
    if (flash?.success) {
      flash.success.forEach(msg => toast.success(msg))
    }
    if (flash?.error) {
      flash.error.forEach(msg => toast.error(msg))
    }
    if (flash?.info) {
      flash.info.forEach(msg => toast.info(msg))
    }
    if (flash?.warning) {
      flash.warning.forEach(msg => toast.warning(msg))
    }
  }, [flash])
}

// Usage in layouts/app-layout.tsx
export function AppLayout({ children }: PropsWithChildren) {
  useFlashMessages() // Auto-displays flash as toasts

  return (
    <div className="h-screen bg-muted/20">
      <Toaster />
      {/* ... */}
    </div>
  )
}
```

### 5. CSRF Helper Usage

**Current State:** Using axios with manual credentials.

**File:** `resources/main.tsx:8`

```tsx
axios.defaults.withCredentials = true
```

**Solution:** Use `litestar-vite` CSRF helpers for fetch-based requests:

```tsx
// For fetch API calls
import { csrfFetch, getCsrfToken } from "litestar-vite-plugin/helpers"

// Automatic CSRF token injection
await csrfFetch("/api/submit", {
  method: "POST",
  body: JSON.stringify(data)
})

// Or get token for custom use
const token = getCsrfToken()
```

---

## Medium Priority Improvements

### 6. Extend Generated Types via Module Augmentation

**Current State:** Duplicate type definitions.

**File:** `resources/types/global.d.ts`

```tsx
// CURRENT - Separate global type
interface InertiaProps extends Page<PageProps> {
  flash: FlashMessages
  errors: Errors & ErrorBag
  csrf_token: string
  auth?: AuthData
  currentTeam?: CurrentTeam
}
```

**Solution:** Use module augmentation with generated types:

```tsx
// resources/types/index.ts
import type { User as GeneratedUser } from "@/lib/generated/page-props"

// Extend the generated User type
declare module "litestar-vite-plugin/inertia" {
  interface User extends GeneratedUser {
    avatarUrl?: string | null
    roles: Array<{ name: string; slug: string }>
    teams: Array<{ id: string; name: string }>
  }

  interface SharedProps {
    currentTeam?: {
      teamId: string
      teamName: string
    }
  }
}

// Now InertiaProps in page-props.ts automatically includes these
```

### 7. Use Generated API Client Consistently

**Current State:** Mixed usage of `router.post` and direct routes.

**File:** `resources/pages/auth/partials/user-login-form.tsx:48`

```tsx
// CURRENT - Using Inertia router with manual route
router.post(route("login"), values, {
  onError: (err) => { ... }
})
```

**For API-only endpoints, use the generated SDK:**

```tsx
import { createUser, listUsers } from "@/lib/generated/api"

// Type-safe API calls with full IntelliSense
const response = await listUsers({
  query: { pageSize: 10, orderBy: "name" }
})

// Response is fully typed
const users = response.data
```

### 8. Route Type Safety for Parameters

**Current State:** Some manual parameter handling.

**Better Approach:**

```tsx
import { route, type RouteParams } from "@/lib/generated/routes"

// Type-safe route with parameters - TypeScript enforces correct params
const teamUrl = route("teams.show", { team_id: teamId })

// This would be a compile error:
// route("teams.show") // Error: team_id is required
// route("teams.show", { wrong_param: "x" }) // Error: wrong property
```

---

## Low Priority / Nice-to-Have

### 9. Inertia Helpers for Page Resolution

**Current State:** Using `resolvePageComponent` correctly.

**File:** `resources/main.tsx:11`

```tsx
resolve: (name) => resolvePageComponent(`./pages/${name}.tsx`, import.meta.glob("./pages/**/*.tsx"))
```

This is correct. No changes needed.

### 10. Consider `unwrapPageProps` for Cleaner Props

For pages that receive complex nested props:

```tsx
import { unwrapPageProps } from "litestar-vite-plugin/inertia-helpers"

export default function TeamShow(rawProps: PagePropsFor<"team/show">) {
  // Automatically handles deferred/lazy props
  const props = unwrapPageProps(rawProps)
}
```

### 11. Lazy Loading with Inertia `lazy()` and `defer()`

**Backend enhancement for performance:**

```python
from litestar_vite.inertia import lazy, defer

@get(component="dashboard")
async def dashboard(self, request: Request) -> dict:
    return {
        "user": user_data,  # Immediate
        "stats": lazy(lambda: get_expensive_stats()),  # Lazy-loaded
        "notifications": defer("notifications"),  # Deferred partial
    }
```

---

## Configuration Review

### Current `.litestar.json` Analysis

Your configuration is mostly good. Suggestions:

```json
{
  "types": {
    "enabled": true,
    "generateRoutes": true,
    "generatePageProps": true,
    "generateSdk": true
  }
}
```


### ViteConfig Review

**File:** `app/config.py:57-76`

```python
vite = ViteConfig(
    inertia=InertiaConfig(
        redirect_unauthorized_to="/login",
        extra_static_page_props={
            "canResetPassword": True,
            "hasTermsAndPrivacyPolicyFeature": True,
            "mustVerifyEmail": True,
        },
        extra_session_page_props={"currentTeam": CurrentTeam},
    ),
)
```

This is well configured. The `extra_session_page_props={"currentTeam": CurrentTeam}` maps the session key to a typed schema, enabling automatic TypeScript type generation.

---

## Migration Checklist

### Phase 1: Critical Fixes
- [ ] Update `litestar-vite` to latest version
- [ ] Regenerate types: `litestar assets generate-types`
- [ ] Fix navbar.tsx to import `isCurrentRoute`
- [ ] Begin removing `from __future__ import annotations` (gradual)

### Phase 2: Type Safety
- [ ] Create `useFlashMessages` hook
- [ ] Update page components to use `PagePropsFor<"component">`
- [ ] Add module augmentation for User/SharedProps types

### Phase 3: API Client
- [ ] Audit API calls and migrate to generated SDK where appropriate
- [ ] Use CSRF helpers for non-Inertia fetches

### Phase 4: Polish
- [ ] Enable Zod generation for form validation
- [ ] Consider lazy/defer for expensive data
- [ ] Add comprehensive TypeScript strict mode

---

## Quick Reference: litestar-vite Imports

```tsx
// Route helpers (from generated routes)
import {
  route,           // Generate URLs
  isCurrentRoute,  // Check current page
  currentRoute,    // Get current route name
  toRoute,         // URL -> route name
  isRoute,         // Check if URL matches pattern
  hasRoute,        // Check if route exists
  getRouteNames,   // List all routes
  routeDefinitions // Raw route metadata
} from "@/lib/generated/routes"

// Page props (from generated)
import type {
  PagePropsFor,    // Props for specific component
  ComponentName,   // Union of component names
  FullSharedProps  // All shared props
} from "@/lib/generated/page-props"

// API client (from generated)
import { listUsers, createUser, ... } from "@/lib/generated/api"

// CSRF utilities
import {
  getCsrfToken,  // Get token string
  csrfFetch,     // Fetch with auto CSRF
  csrfHeaders    // Headers object with token
} from "litestar-vite-plugin/helpers"

// Inertia helpers
import {
  resolvePageComponent,  // Page resolution
  unwrapPageProps        // Props unwrapping
} from "litestar-vite-plugin/inertia-helpers"
```

---

## Questions?

Reach out via:
- GitHub Issues: https://github.com/litestar-org/litestar-vite/issues
- Discord: Litestar server

---

*Generated by litestar-vite analysis tool*

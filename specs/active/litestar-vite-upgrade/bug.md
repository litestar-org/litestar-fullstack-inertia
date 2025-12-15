# Bug Report: ViteSPAHandler not initialized in hybrid/inertia mode

## Status: RESOLVED

**Fixed in**: litestar-vite v0.15.0-alpha.7

The ViteSPAHandler initialization issue and all related bugs have been addressed in the alpha 7 release. See PR #127 for the security and quality fixes.

## Issues Fixed in Alpha 7

| Issue | Title | Status |
|-------|-------|--------|
| [#122](https://github.com/litestar-org/litestar-vite/issues/122) | HTTPException converted to 500 for non-Inertia requests | Fixed |
| [#123](https://github.com/litestar-org/litestar-vite/issues/123) | Security: Open redirect vulnerability in InertiaBack via Referer header | Fixed |
| [#124](https://github.com/litestar-org/litestar-vite/issues/124) | Exception handler crashes on empty extras list (IndexError) | Fixed |
| [#125](https://github.com/litestar-org/litestar-vite/issues/125) | InertiaPlugin lookup crashes if plugin not registered | Fixed |
| [#126](https://github.com/litestar-org/litestar-vite/issues/126) | Request cookies incorrectly passed to redirect responses | Fixed |

## Changes Applied to This Project

1. **Removed HTTPException handler workaround** from `app/server/core.py`
   - The `_http_exception_handler` function was a workaround for issue #122
   - Now handled correctly by litestar-vite

2. **Updated dependency** to `litestar-vite>=0.15.0a7`

3. **Deleted** `specs/litestar-vite-bugs.md` (no longer needed)

# Inertia SSR Architecture Analysis

## Current Issue

The Vite proxy middleware is failing with 500 errors when trying to proxy requests like `/static/@vite/client` to the Vite dev server. This prevents the browser from loading any JavaScript, causing the page to hang.

## How Laravel/Inertia Works

### Two Rendering Modes

#### 1. Client-Side Rendering (CSR) - No SSR
- Vite builds the app to static JS/CSS bundles
- Server returns HTML template with `data-page` attribute containing serialized props
- Browser loads JS bundles and React/Vue hydrates the page
- **This is what litestar-fullstack-inertia currently uses**

#### 2. Server-Side Rendering (SSR)
- Requires a separate Node.js SSR server running (`php artisan inertia:start-ssr`)
- PHP calls the Node SSR server internally (typically port 13714) to pre-render components
- The SSR server returns fully rendered HTML
- PHP sends complete HTML to browser with hydration data
- Browser hydrates the pre-rendered HTML

### Key Insight: Connection Flow in Production

**Browser connects to PHP/Python (port 80/443) - NOT Vite**

```
┌─────────┐      HTTP       ┌─────────────┐     Internal     ┌─────────────┐
│ Browser │ ───────────────>│ PHP/Python  │ ───────────────> │ Node SSR    │
│         │<─────────────── │ (port 80)   │ <─────────────── │ (port 13714)│
└─────────┘   Full HTML     └─────────────┘   Rendered HTML  └─────────────┘
```

**Vite is NOT involved in production** - it's purely a dev/build tool:
- **Dev**: Vite dev server runs for HMR, proxy forwards asset requests
- **Build**: `vite build` creates static JS/CSS bundles
- **Production**: Only static bundles are served, no Vite process

## Modes Breakdown

### Development Mode (Current Issue)

```
┌─────────┐     /landing     ┌─────────────┐
│ Browser │ ────────────────>│  Litestar   │──> Returns HTML with data-page
│         │                  │  (port 8088)│
│         │  /static/*.js    │             │
│         │ ────────────────>│   Proxy     │──> Forward to Vite dev server
│         │<──────────────── │  Middleware │<── (port 5173)
└─────────┘    JS bundles    └─────────────┘
```

**Problem**: The proxy middleware is returning 500 errors instead of forwarding to Vite.

### Production Mode (CSR - No SSR)

```
┌─────────┐     /landing     ┌─────────────┐
│ Browser │ ────────────────>│  Litestar   │──> Returns HTML with data-page
│         │                  │  (port 80)  │
│         │  /static/*.js    │             │
│         │ ────────────────>│ Static File │──> Serve from bundle_dir
│         │<──────────────── │   Router    │
└─────────┘    JS bundles    └─────────────┘
```

**No proxy needed** - static files served directly from `app/domain/web/public/assets/`

### Production Mode (With SSR)

```
┌─────────┐     /landing     ┌─────────────┐     HTTP        ┌─────────────┐
│ Browser │ ────────────────>│  Litestar   │───────────────> │ Node SSR    │
│         │<──────────────── │  (port 80)  │ <────────────── │ (port 13714)│
└─────────┘  Full HTML +     └─────────────┘  Rendered HTML  └─────────────┘
             hydration data        │
                                   │  /static/*.js
                                   v
                            Static File Router
                            (bundle_dir assets)
```

**Requires**: Internal HTTP client to call Node SSR server (similar to proxy but server-to-server)

## What litestar-vite Needs

### For Development
- **ViteProxyMiddleware** (whitelist mode): Forward `/static/*`, `/resources/*`, `/@vite/*` to Vite dev server
- Currently broken - needs debugging

### For Production (CSR)
- **Static file router**: Serve built assets from `bundle_dir`
- **No proxy needed**
- Already working via `create_static_files_router`

### For Production (SSR) - Future
- **SSR Client**: HTTP client to call Node SSR server
- Similar to proxy but:
  - Only called for initial page loads (not XHR Inertia requests)
  - Sends page props to SSR server
  - Receives rendered HTML
  - Injects into response
- Would need new config: `ssr_server_url`, `ssr_enabled`

## Bug Found: ViteProxyMiddleware Response Body Access After Client Close

### Location

**File**: `litestar-vite/src/py/litestar_vite/plugin.py`
**Lines**: 547-569
**Class**: `ViteProxyMiddleware`

### Root Cause

The proxy middleware accesses `upstream_resp.content` **after** the `httpx.AsyncClient` context manager has exited:

```python
# litestar_vite/plugin.py lines 547-569
async with httpx.AsyncClient(http2=http2_enabled) as client:
    try:
        upstream_resp = await client.request(method, url, headers=headers, content=body, timeout=10.0)
    except httpx.HTTPError as exc:  # pragma: no cover
        await send({
            "type": "http.response.start",
            "status": 502,
            "headers": [(b"content-type", b"text/plain")],
        })
        await send({"type": "http.response.body", "body": str(exc).encode()})
        return

# BUG: These lines are OUTSIDE the context manager!
response_headers = [(k.encode(), v.encode()) for k, v in upstream_resp.headers.items()]
await send({
    "type": "http.response.start",
    "status": upstream_resp.status_code,
    "headers": response_headers,
})
await send({"type": "http.response.body", "body": upstream_resp.content})  # <-- Fails here!
```

For large responses (like the 182KB `@vite/client`), the response body isn't fully buffered before the connection closes, causing:

```text
LitestarException: Exception caught after response started
```

### Error Log Evidence

```text
receive_response_headers.complete return_value=(b'HTTP/1.1', 200, b'OK', [..., (b'Content-Length', b'182729')])
receive_response_body.started ...
receive_response_body.complete
response_closed.started
response_closed.complete
close.started
close.complete
[error] Exception caught after response started
```

The response body is "complete" but the connection is closed before content is fully read.

### Fix Required

Move the response sending **inside** the context manager so content is read while the client is still open:

```python
# litestar_vite/plugin.py - FIXED version
async with httpx.AsyncClient(http2=http2_enabled) as client:
    try:
        upstream_resp = await client.request(method, url, headers=headers, content=body, timeout=10.0)
    except httpx.HTTPError as exc:  # pragma: no cover
        await send({
            "type": "http.response.start",
            "status": 502,
            "headers": [(b"content-type", b"text/plain")],
        })
        await send({"type": "http.response.body", "body": str(exc).encode()})
        return

    # FIX: Read content and send response INSIDE the context manager
    response_headers = [(k.encode(), v.encode()) for k, v in upstream_resp.headers.items()]
    await send({
        "type": "http.response.start",
        "status": upstream_resp.status_code,
        "headers": response_headers,
    })
    await send({"type": "http.response.body", "body": upstream_resp.content})
```

### Workaround

None currently - this is a litestar-vite bug that needs to be fixed upstream in `litestar-vite`

## References

- [Inertia.js Server-side rendering (SSR)](https://inertiajs.com/server-side-rendering)
- [Laravel Asset Bundling (Vite)](https://laravel.com/docs/12.x/vite)
- [Using Inertia SSR - Fly.io Docs](https://fly.io/docs/laravel/advanced-guides/using-inertia-ssr/)

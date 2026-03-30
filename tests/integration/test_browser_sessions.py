from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Awaitable, Callable

    from litestar import Litestar
    from litestar.types import Receive, Scope, Send

pytestmark = pytest.mark.anyio


def _page_content(response_json: dict[str, Any]) -> dict[str, Any]:
    props = response_json["props"]
    return props.get("content", props)


def _fresh_state_lifespan_middleware(
    app: Litestar, initial_state: dict[str, Any],
) -> Callable[[Scope, Receive, Send], Awaitable[None]]:
    async def app_with_state(scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            scope["state"] = dict(initial_state)
        else:
            scope["state"] = initial_state
        await app(scope, receive, send)

    return app_with_state


@asynccontextmanager
async def _managed_clients(app: Litestar) -> AsyncIterator[tuple[AsyncClient, AsyncClient]]:
    manager = LifespanManager(app)  # type: ignore[arg-type]
    manager.app = _fresh_state_lifespan_middleware(app, manager._state)  # type: ignore[assignment]

    async with manager:
        async with AsyncClient(
            transport=ASGITransport(app=manager.app),
            base_url="http://testserver",
            timeout=10,
        ) as first, AsyncClient(
            transport=ASGITransport(app=manager.app),
            base_url="http://testserver",
            timeout=10,
        ) as second:
            yield first, second


async def _login_headers(
    client: AsyncClient, username: str, password: str, *, inertia: bool = False,
) -> dict[str, str]:
    client.cookies.clear()
    response = await client.get("/login")
    csrf_token: str = response.cookies.get("XSRF-TOKEN") or ""
    headers: dict[str, str] = {
        "X-XSRF-TOKEN": csrf_token,
        "Content-Type": "application/json",
    }
    response = await client.post(
        "/login/",
        json={"username": username, "password": password},
        headers=headers,
        follow_redirects=False,
    )
    assert response.status_code == 303

    csrf_token = response.cookies.get("XSRF-TOKEN") or csrf_token
    cookies_snapshot = dict(client.cookies.items())
    result = {
        "X-XSRF-TOKEN": csrf_token,
        "Content-Type": "application/json",
        "Cookie": "; ".join(f"{key}={value}" for key, value in cookies_snapshot.items()),
    }
    if inertia:
        result["X-Inertia"] = "true"
    return result


async def test_browser_sessions_list_and_logout_others(app: Litestar) -> None:
    async with _managed_clients(app) as (first, second):
        first_headers = await _login_headers(first, "user@example.com", "Test_Password2!", inertia=True)
        second_headers = await _login_headers(second, "user@example.com", "Test_Password2!", inertia=True)

        await first.get("/profile/", headers=first_headers)
        await second.get("/profile/", headers=second_headers)

        response = await first.get("/profile/", headers=first_headers)
        assert response.status_code == 200
        sessions = _page_content(response.json())["browserSessions"]
        assert len(sessions) == 2
        assert len([session for session in sessions if session["isCurrent"]]) == 1

        response = await first.post(
            "/profile/browser-sessions/logout-others/",
            headers=first_headers,
            json={"password": "Test_Password2!"},
            follow_redirects=False,
        )
        assert response.status_code == 303

        response = await first.get("/profile/", headers=first_headers)
        assert response.status_code == 200
        sessions = _page_content(response.json())["browserSessions"]
        assert len(sessions) == 1
        assert sessions[0]["isCurrent"] is True

        response = await second.get("/profile/", headers=second_headers, follow_redirects=False)
        assert response.status_code in (302, 303, 307)
        assert "/login" in response.headers.get("location", "")


async def test_browser_sessions_logout_others_requires_valid_password(app: Litestar) -> None:
    async with _managed_clients(app) as (first, second):
        first_headers = await _login_headers(first, "user@example.com", "Test_Password2!", inertia=True)
        second_headers = await _login_headers(second, "user@example.com", "Test_Password2!", inertia=True)

        await first.get("/profile/", headers=first_headers)
        await second.get("/profile/", headers=second_headers)

        response = await first.post(
            "/profile/browser-sessions/logout-others/",
            headers=first_headers,
            json={"password": "wrong-password"},
            follow_redirects=False,
        )
        assert response.status_code in (400, 422)

        response = await second.get("/profile/", headers=second_headers)
        assert response.status_code == 200

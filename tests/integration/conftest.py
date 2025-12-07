from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from advanced_alchemy.base import UUIDAuditBase
from advanced_alchemy.utils.fixtures import open_fixture_async
from httpx import ASGITransport, AsyncClient
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.domain.accounts.services import RoleService, UserService
from app.domain.teams.services import TeamService
from app.lib.settings import get_settings
from app.server.plugins import alchemy

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, AsyncIterator, Awaitable, Callable

    from litestar import Litestar
    from litestar.types import Receive, Scope, Send

    from app.db.models import Team, User

here = Path(__file__).parent
pytestmark = pytest.mark.anyio


@pytest.fixture(name="engine", autouse=True)
async def fx_engine(
    postgres_docker_ip: str,
    postgres_service: None,
    postgres_port: int,
    postgres_user: str,
    postgres_password: str,
    postgres_database: str,
) -> AsyncEngine:
    """Postgresql instance for end-to-end testing.

    Returns:
        Async SQLAlchemy engine instance.
    """
    return create_async_engine(
        URL(
            drivername="postgresql+asyncpg",
            username=postgres_user,
            password=postgres_password,
            host=postgres_docker_ip,
            port=postgres_port,
            database=postgres_database,
            query={},  # type:ignore[arg-type]
        ),
        echo=False,
        poolclass=NullPool,
    )


@pytest.fixture(name="sessionmaker")
def fx_session_maker_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture(name="session")
async def fx_session(sessionmaker: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession, None]:
    async with sessionmaker() as session:
        yield session


@pytest.fixture(autouse=True)
async def _seed_db(
    engine: AsyncEngine,
    sessionmaker: async_sessionmaker[AsyncSession],
    raw_users: list[User | dict[str, Any]],
    raw_teams: list[Team | dict[str, Any]],
) -> AsyncIterator[None]:
    """Populate test database with.

    Args:
        engine: The SQLAlchemy engine instance.
        sessionmaker: The SQLAlchemy sessionmaker factory.
        raw_users: Test users to add to the database
        raw_teams: Test teams to add to the database

    """

    settings = get_settings()
    fixtures_path = Path(settings.db.FIXTURE_PATH)
    metadata = UUIDAuditBase.registry.metadata
    async with engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
        await conn.run_sync(metadata.create_all)
    async with RoleService.new(sessionmaker()) as service:
        fixture = await open_fixture_async(fixtures_path, "role")
        for obj in fixture:
            _ = await service.repository.get_or_upsert(match_fields="name", upsert=True, **obj)
        await service.repository.session.commit()
    async with UserService.new(sessionmaker()) as users_service:
        await users_service.create_many(raw_users, auto_commit=True)
    async with TeamService.new(sessionmaker()) as teams_services:
        for obj in raw_teams:
            await teams_services.create(obj)
        await teams_services.repository.session.commit()

    yield


@pytest.fixture(autouse=True)
def _patch_db(
    app: "Litestar",
    engine: AsyncEngine,
    sessionmaker: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(alchemy._config, "session_maker", sessionmaker)
    if isinstance(alchemy._config, list):
        monkeypatch.setitem(app.state, alchemy._config[0].engine_app_state_key, engine)
        monkeypatch.setitem(
            app.state,
            alchemy._config[0].session_maker_app_state_key,
            async_sessionmaker(bind=engine, expire_on_commit=False),
        )
    else:
        monkeypatch.setitem(app.state, alchemy._config.engine_app_state_key, engine)
        monkeypatch.setitem(
            app.state,
            alchemy._config.session_maker_app_state_key,
            async_sessionmaker(bind=engine, expire_on_commit=False),
        )


def _fresh_state_lifespan_middleware(
    app: "Litestar", initial_state: dict[str, Any],
) -> Callable[["Scope", "Receive", "Send"], Awaitable[None]]:
    """Middleware that creates a fresh state dict for each HTTP request.

    This prevents state bleeding between requests when using LifespanManager,
    which normally shares the same state dict across all requests.
    """

    async def app_with_state(scope: "Scope", receive: "Receive", send: "Send") -> None:
        if scope["type"] == "http":
            # Create a copy of initial_state for each HTTP request
            # This prevents _ls_connection_state from being reused
            scope["state"] = dict(initial_state)
        else:
            # Lifespan events can share state
            scope["state"] = initial_state
        await app(scope, receive, send)

    return app_with_state


@pytest.fixture(name="client")
async def fx_client(app: Litestar) -> AsyncIterator[AsyncClient]:
    """Async client that calls requests on the app.

    Uses asgi-lifespan LifespanManager to ensure app lifespan hooks run
    (e.g., ViteSPAHandler initialization), with a custom middleware that
    prevents state bleeding between requests.
    """
    from asgi_lifespan import LifespanManager

    manager = LifespanManager(app)
    # Replace the wrapped app with one that creates fresh state per request
    manager.app = _fresh_state_lifespan_middleware(app, manager._state)

    async with manager, AsyncClient(
        transport=ASGITransport(app=manager.app),
        base_url="http://testserver",
        timeout=10,
    ) as client:  # type: ignore[arg-type]
        yield client


async def _get_auth_headers(client: AsyncClient, username: str, password: str, *, inertia: bool = False) -> dict[str, str]:
    """Helper to login a user and return auth headers with CSRF token.

    Args:
        client: The test client.
        username: The username to login with.
        password: The password to login with.
        inertia: If True, include X-Inertia header for Inertia page routes.
    """
    # Clear existing cookies to ensure fresh session for each login
    client.cookies.clear()

    # First get CSRF token
    response = await client.get("/login")
    csrf_token = response.cookies.get("XSRF-TOKEN", "")

    headers = {
        "X-XSRF-TOKEN": csrf_token,
        "Content-Type": "application/json",
    }

    # Login the user
    response = await client.post(
        "/login/",
        json={"username": username, "password": password},
        headers=headers,
        follow_redirects=False,
    )

    # Get updated CSRF token after login
    csrf_token = response.cookies.get("XSRF-TOKEN", csrf_token)

    # Capture cookies at this moment - create a copy to avoid mutation issues
    cookies_snapshot = dict(client.cookies.items())

    result = {
        "X-XSRF-TOKEN": csrf_token,
        "Content-Type": "application/json",
        "Cookie": "; ".join([f"{k}={v}" for k, v in cookies_snapshot.items()]),
    }

    if inertia:
        result["X-Inertia"] = "true"

    return result


@pytest.fixture(name="superuser_token_headers")
async def fx_superuser_token_headers(client: AsyncClient) -> dict[str, str]:
    """Auth headers for superuser (API routes without Inertia)."""
    return await _get_auth_headers(client, "superuser@example.com", "Test_Password1!")


@pytest.fixture(name="user_token_headers")
async def fx_user_token_headers(client: AsyncClient) -> dict[str, str]:
    """Auth headers for regular user (API routes without Inertia)."""
    return await _get_auth_headers(client, "user@example.com", "Test_Password2!")


@pytest.fixture(name="superuser_inertia_headers")
async def fx_superuser_inertia_headers(client: AsyncClient) -> dict[str, str]:
    """Auth headers for superuser (Inertia page routes)."""
    return await _get_auth_headers(client, "superuser@example.com", "Test_Password1!", inertia=True)


@pytest.fixture(name="user_inertia_headers")
async def fx_user_inertia_headers(client: AsyncClient) -> dict[str, str]:
    """Auth headers for regular user (Inertia page routes)."""
    return await _get_auth_headers(client, "user@example.com", "Test_Password2!", inertia=True)

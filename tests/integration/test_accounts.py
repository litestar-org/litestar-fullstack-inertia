from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def test_update_user_no_auth(client: "AsyncClient") -> None:
    """Unauthenticated requests to API routes should return 401."""
    response = await client.patch("/api/users/97108ac1-ffcb-411d-8b1e-d9183399f63b", json={"name": "TEST UPDATE"})
    assert response.status_code == 401
    response = await client.post(
        "/api/users/",
        json={"name": "A User", "email": "new-user@example.com", "password": "S3cret!"},
    )
    assert response.status_code == 401
    response = await client.get("/api/users/97108ac1-ffcb-411d-8b1e-d9183399f63b")
    assert response.status_code == 401
    response = await client.get("/api/users")
    assert response.status_code == 401
    response = await client.delete("/api/users/97108ac1-ffcb-411d-8b1e-d9183399f63b")
    assert response.status_code == 401


async def test_accounts_list(client: "AsyncClient", superuser_token_headers: dict[str, str]) -> None:
    """Superuser can list all users."""
    response = await client.get("/api/users", headers=superuser_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert int(data["total"]) > 0


async def test_accounts_get(client: "AsyncClient", superuser_token_headers: dict[str, str]) -> None:
    """Superuser can get a specific user."""
    response = await client.get("/api/users/97108ac1-ffcb-411d-8b1e-d9183399f63b", headers=superuser_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "superuser@example.com"


async def test_accounts_create(client: "AsyncClient", superuser_token_headers: dict[str, str]) -> None:
    """Superuser can create a new user."""
    response = await client.post(
        "/api/users",
        json={"name": "A User", "email": "new-user@example.com", "password": "S3cret!"},
        headers=superuser_token_headers,
    )
    assert response.status_code == 201


async def test_accounts_update(client: "AsyncClient", superuser_token_headers: dict[str, str]) -> None:
    """Superuser can update a user."""
    response = await client.patch(
        "/api/users/5ef29f3c-3560-4d15-ba6b-a2e5c721e4d2",
        json={
            "name": "Name Changed",
        },
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Name Changed"


async def test_accounts_delete(client: "AsyncClient", superuser_token_headers: dict[str, str], superuser_inertia_headers: dict[str, str]) -> None:
    """Superuser can delete a user."""
    response = await client.delete(
        "/api/users/5ef29f3c-3560-4d15-ba6b-a2e5c721e4d2",
        headers=superuser_token_headers,
    )
    assert response.status_code == 204
    # Ensure we didn't cascade delete the teams the user owned
    response = await client.get(
        "/teams/test-team/",
        headers=superuser_inertia_headers,
    )
    assert response.status_code == 200


async def test_accounts_with_incorrect_role(client: "AsyncClient", user_token_headers: dict[str, str]) -> None:
    """Regular user should get 403 for admin-only user operations."""
    response = await client.patch(
        "/api/users/97108ac1-ffcb-411d-8b1e-d9183399f63b",
        json={"name": "TEST UPDATE"},
        headers=user_token_headers,
    )
    assert response.status_code == 403
    response = await client.post(
        "/api/users/",
        json={"name": "A User", "email": "new-user@example.com", "password": "S3cret!"},
        headers=user_token_headers,
    )
    assert response.status_code == 403
    response = await client.get("/api/users/97108ac1-ffcb-411d-8b1e-d9183399f63b", headers=user_token_headers)
    assert response.status_code == 403
    response = await client.get("/api/users", headers=user_token_headers)
    assert response.status_code == 403
    response = await client.delete("/api/users/97108ac1-ffcb-411d-8b1e-d9183399f63b", headers=user_token_headers)
    assert response.status_code == 403

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient


pytestmark = pytest.mark.anyio


async def test_superuser_role_access(
    client: "AsyncClient",
    user_inertia_headers: dict[str, str],
    superuser_token_headers: dict[str, str],
) -> None:
    """Test that assigning/revoking superuser role changes team visibility.

    Note: Test users are created without roles, so they start with empty roles.
    After superuser role is assigned and revoked, they return to having no roles.
    """
    # User should only see their own teams to start (they own 1 team)
    response = await client.get("/teams", headers=user_inertia_headers)
    assert response.status_code == 200
    data = response.json()
    assert "props" in data
    # Props contains 'items' from OffsetPagination - count the items
    assert len(data["props"]["items"]) == 1

    # Assign the superuser role
    response = await client.post(
        "/api/roles/superuser/assign",
        json={"userName": "user@example.com"},
        headers=superuser_token_headers,
    )
    assert response.status_code == 201
    assert response.json()["message"] == "Successfully assigned the 'superuser' role to user@example.com."

    # User can now update a team they don't own
    response = await client.patch(
        "/teams/81108ac1-ffcb-411d-8b1e-d91833999999",
        json={"name": "TEST UPDATE"},
        headers=user_inertia_headers,
    )
    assert response.status_code == 200

    # User can now retrieve any team
    response = await client.get("/teams/81108ac1-ffcb-411d-8b1e-d91833999999", headers=user_inertia_headers)
    assert response.status_code == 200

    # User can now see all teams
    response = await client.get("/teams", headers=user_inertia_headers)
    assert response.status_code == 200
    data = response.json()
    # OffsetPagination returns items list - count them
    assert len(data["props"]["items"]) == 3

    # Superuser should see all teams
    superuser_response = await client.get("/teams", headers={
        **superuser_token_headers,
        "X-Inertia": "true",
    })
    assert superuser_response.status_code == 200
    superuser_data = superuser_response.json()
    assert len(superuser_data["props"]["items"]) == 3

    # Revoke the superuser role
    response = await client.post(
        "/api/roles/superuser/revoke",
        json={"userName": "user@example.com"},
        headers=superuser_token_headers,
    )
    assert response.status_code == 201

    # User can no longer see all teams - only their own
    # (they still own 1 team, so they can still see that one)
    response = await client.get("/teams", headers=user_inertia_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["props"]["items"]) == 1

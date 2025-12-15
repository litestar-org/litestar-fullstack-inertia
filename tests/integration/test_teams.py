from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def test_teams_with_no_auth(client: "AsyncClient") -> None:
    """Unauthenticated requests should be rejected or redirect to login.

    Routes with Inertia components redirect to login (303 for non-GET, 307 for GET).
    Routes without components return 401.
    """
    # PATCH with component="team/edit" redirects to login (303 See Other)
    response = await client.patch("/teams/97108ac1-ffcb-411d-8b1e-d9183399f63b", json={"name": "TEST UPDATE"})
    assert response.status_code == 303

    # POST without component returns 401 (not authorized)
    response = await client.post(
        "/teams",
        json={"name": "A User", "email": "new-user@example.com", "password": "S3cret!"},
    )
    assert response.status_code == 401

    # DELETE without component returns 401 (status_code=303 only applies to success)
    response = await client.delete("/teams/97108ac1-ffcb-411d-8b1e-d9183399f63b")
    assert response.status_code == 401

    # GET with component="team/show" redirects to login (307 Temporary Redirect)
    response = await client.get("/teams/97108ac1-ffcb-411d-8b1e-d9183399f63b")
    assert response.status_code == 307
    # GET with component="team/list" redirects to login (307 Temporary Redirect)
    response = await client.get("/teams")
    assert response.status_code == 307


async def test_teams_with_incorrect_role(client: "AsyncClient", user_inertia_headers: dict[str, str]) -> None:
    """User without team access should be redirected for unauthorized team operations.

    Note: Inertia uses 307 for GET (preserves method) and 303 for other methods.
    """
    # User cannot update a team they don't have admin access to
    response = await client.patch(
        "/teams/81108ac1-ffcb-411d-8b1e-d91833999999",
        json={"name": "TEST UPDATE"},
        headers=user_inertia_headers,
    )
    assert response.status_code == 303  # PATCH redirects to GET via 303

    # User can create a new team (they become the owner)
    response = await client.post(
        "/teams",
        json={"name": "A new team."},
        headers=user_inertia_headers,
    )
    assert response.status_code == 303  # POST redirects to GET via 303

    # User cannot view a team they're not a member of
    response = await client.get("/teams/81108ac1-ffcb-411d-8b1e-d91833999999", headers=user_inertia_headers)
    assert response.status_code == 307  # GET preserves method via 307

    # User can view the teams list (filtered to their teams)
    response = await client.get("/teams", headers=user_inertia_headers)
    assert response.status_code == 200

    # User cannot delete a team they don't own
    response = await client.delete("/teams/81108ac1-ffcb-411d-8b1e-d91833999999", headers=user_inertia_headers)
    assert response.status_code == 303  # DELETE redirects to GET via 303


async def test_teams_list(client: "AsyncClient", superuser_inertia_headers: dict[str, str]) -> None:
    """Superuser can list all teams via Inertia endpoint."""
    response = await client.get("/teams", headers=superuser_inertia_headers)
    assert response.status_code == 200
    data = response.json()
    # Inertia responses wrap handler return value in props
    # The OffsetPagination items are serialized directly to props.items
    assert "props" in data
    props = data["props"]
    assert "items" in props
    assert len(props["items"]) > 0


async def test_teams_get(client: "AsyncClient", superuser_inertia_headers: dict[str, str]) -> None:
    """Superuser can get a specific team via Inertia endpoint."""
    response = await client.get("/teams/97108ac1-ffcb-411d-8b1e-d9183399f63b", headers=superuser_inertia_headers)
    assert response.status_code == 200
    data = response.json()
    # Inertia responses wrap handler return value in props.content
    assert "props" in data
    props = data["props"]
    assert "content" in props
    assert props["content"]["name"] == "Test Team"


async def test_teams_create(client: "AsyncClient", superuser_inertia_headers: dict[str, str]) -> None:
    """Superuser can create a team."""
    response = await client.post(
        "/teams",
        json={"name": "My First Team", "tags": ["cool tag"]},
        headers=superuser_inertia_headers,
    )
    # Inertia create returns a redirect (303)
    assert response.status_code == 303


async def test_teams_update(client: "AsyncClient", superuser_inertia_headers: dict[str, str]) -> None:
    """Superuser can update a team via Inertia endpoint."""
    response = await client.patch(
        "/teams/97108ac1-ffcb-411d-8b1e-d9183399f63b",
        json={"name": "Name Changed"},
        headers=superuser_inertia_headers,
    )
    assert response.status_code == 200


async def test_teams_delete(
    client: "AsyncClient", superuser_inertia_headers: dict[str, str], superuser_token_headers: dict[str, str],
) -> None:
    """Superuser can delete a team."""
    response = await client.delete(
        "/teams/81108ac1-ffcb-411d-8b1e-d91833999999",
        headers=superuser_inertia_headers,
    )
    # Inertia delete returns a redirect (303)
    assert response.status_code == 303
    # Ensure we didn't cascade delete the users that were members of the team
    response = await client.get(
        "/api/users/5ef29f3c-3560-4d15-ba6b-a2e5c721e999",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200

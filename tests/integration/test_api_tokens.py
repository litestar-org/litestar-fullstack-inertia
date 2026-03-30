from __future__ import annotations

from typing import Any

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


def _page_content(response_json: dict[str, Any]) -> dict[str, Any]:
    props = response_json["props"]
    return props.get("content", props)


async def test_api_tokens_page_create_revoke_and_bearer_usage(
    client: AsyncClient,
    user_inertia_headers: dict[str, str],
    user_token_headers: dict[str, str],
) -> None:
    response = await client.get("/api-tokens/", headers=user_inertia_headers)
    assert response.status_code == 200
    content = _page_content(response.json())
    assert content["tokens"] == []
    assert content["availableAbilities"]

    response = await client.post(
        "/api-tokens/",
        headers=user_token_headers,
        json={"name": "CLI", "abilities": ["teams:read"]},
    )
    assert response.status_code in (200, 201)
    created = response.json()
    assert created["token"].startswith("lst_")
    assert created["item"]["name"] == "CLI"
    token_id = created["item"]["id"]

    bearer_headers = {"Authorization": f"Bearer {created['token']}", "X-Inertia": "true"}
    response = await client.get("/teams/", headers=bearer_headers, follow_redirects=False)
    assert response.status_code == 200

    response = await client.get("/api-tokens/", headers=user_inertia_headers)
    assert response.status_code == 200
    tokens = _page_content(response.json())["tokens"]
    current_token = next(token for token in tokens if token["id"] == token_id)
    assert current_token["lastUsedAt"] is not None

    response = await client.delete(f"/api-tokens/{token_id}/", headers=user_token_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "API token revoked."

    response = await client.get("/api/users", headers={"Authorization": f"Bearer {created['token']}"}, follow_redirects=False)
    assert response.status_code == 401


async def test_api_tokens_enforce_route_abilities(
    client: AsyncClient,
    user_token_headers: dict[str, str],
) -> None:
    response = await client.post(
        "/api-tokens/",
        headers=user_token_headers,
        json={"name": "Profile only", "abilities": ["profile:read"]},
    )
    assert response.status_code in (200, 201)
    token = response.json()["token"]

    response = await client.get(
        "/teams/",
        headers={"Authorization": f"Bearer {token}", "X-Inertia": "true"},
        follow_redirects=False,
    )
    assert response.status_code == 403


async def test_invalid_bearer_token_is_unauthorized(client: AsyncClient) -> None:
    response = await client.get("/api/users", headers={"Authorization": "Bearer invalid-token"}, follow_redirects=False)
    assert response.status_code == 401

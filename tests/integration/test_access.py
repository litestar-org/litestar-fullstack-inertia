import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def get_csrf_token(client: AsyncClient, path: str = "/login/") -> str:
    """Get CSRF token by visiting a page first."""
    response = await client.get(path, follow_redirects=True)
    return response.cookies.get("XSRF-TOKEN") or client.cookies.get("XSRF-TOKEN") or ""


@pytest.mark.parametrize(
    ("username", "password", "expected_redirect"),
    (
        ("superuser@example.com", "Test_Password1!", True),
        ("user@example.com", "Test_Password2!", True),
    ),
)
async def test_user_login(client: AsyncClient, username: str, password: str, expected_redirect: bool) -> None:
    """Test successful login redirects to dashboard."""
    # Get CSRF token first
    csrf_token = await get_csrf_token(client)
    headers = {"X-XSRF-TOKEN": csrf_token} if csrf_token else {}

    response = await client.post(
        "/login/",
        json={"username": username, "password": password},
        headers=headers,
        follow_redirects=False,
    )
    # Inertia login returns 303 redirect on success
    assert response.status_code == 303
    assert "/dashboard" in response.headers.get("location", "")


@pytest.mark.parametrize(
    ("username", "password"),
    (
        ("superuser@example1.com", "Test_Password1!"),  # wrong email
        ("user@example.com", "Test_Password1!"),  # wrong password
        ("inactive@example.com", "Old_Password2!"),  # inactive user
    ),
)
async def test_user_login_failure(client: AsyncClient, username: str, password: str) -> None:
    """Test failed login attempts.

    With Inertia.js, failed login redirects back to login page with flash message.
    The key security check is that we don't get redirected to dashboard.
    """
    # Get CSRF token first
    csrf_token = await get_csrf_token(client)
    headers: dict[str, str] = {"X-XSRF-TOKEN": csrf_token} if csrf_token else {}

    response = await client.post(
        "/login/",
        json={"username": username, "password": password},
        headers=headers,
        follow_redirects=False,
    )
    # Inertia redirects failed login with flash message (303)
    assert response.status_code == 303, f"Expected 303 redirect, got {response.status_code}"
    # Critical security check: we must NOT be redirected to dashboard
    location = response.headers.get("location", "")
    assert "/dashboard" not in location, "Security violation: redirected to dashboard on failed login"


@pytest.mark.parametrize(
    ("username", "password"),
    (
        ("superuser@example.com", "Test_Password1!"),
    ),
)
async def test_user_logout(client: AsyncClient, username: str, password: str) -> None:
    """Test logout flow."""
    # Get CSRF token first
    csrf_token = await get_csrf_token(client)
    headers = {"X-XSRF-TOKEN": csrf_token} if csrf_token else {}

    # Login first
    response = await client.post(
        "/login/",
        json={"username": username, "password": password},
        headers=headers,
        follow_redirects=False,
    )
    assert response.status_code == 303

    # Logout - use CSRF token from client cookies (already set during login flow)
    csrf_token = client.cookies.get("XSRF-TOKEN") or ""
    headers = {"X-XSRF-TOKEN": csrf_token} if csrf_token else {}

    response = await client.post("/logout/", headers=headers, follow_redirects=False)
    assert response.status_code == 303
    assert "/login" in response.headers.get("location", "")

"""End-to-end tests for the password auth flow, session lifecycle, and CSRF."""

from tests.conftest import csrf_header

SIGNUP = "/auth/signup"
LOGIN = "/auth/login"
REFRESH = "/auth/refresh"
LOGOUT = "/auth/logout"
ME = "/auth/me"

USER = {"email": "alice@example.com", "password": "supersecret123", "full_name": "Alice"}


async def test_signup_sets_cookies_and_returns_user(client):
    r = await client.post(SIGNUP, json=USER)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["email"] == "alice@example.com"
    assert body["is_verified"] is False
    # Cookies issued
    assert client.cookies.get("access_token")
    assert client.cookies.get("refresh_token")
    assert client.cookies.get("csrf_token")


async def test_duplicate_email_rejected(client):
    await client.post(SIGNUP, json=USER)
    r = await client.post(SIGNUP, json=USER)
    assert r.status_code == 400
    assert "already exists" in r.json()["detail"]


async def test_me_requires_auth(client):
    r = await client.get(ME)
    assert r.status_code == 401


async def test_login_then_me(client):
    await client.post(SIGNUP, json=USER)
    # Fresh client-less state: clear cookies to simulate a returning visitor.
    client.cookies.clear()
    r = await client.post(LOGIN, json={"email": USER["email"], "password": USER["password"]})
    assert r.status_code == 200, r.text
    me = await client.get(ME)
    assert me.status_code == 200
    assert me.json()["email"] == USER["email"]


async def test_login_wrong_password(client):
    await client.post(SIGNUP, json=USER)
    r = await client.post(LOGIN, json={"email": USER["email"], "password": "wrongpass123"})
    assert r.status_code == 401


async def test_refresh_requires_csrf(client):
    await client.post(SIGNUP, json=USER)
    # No CSRF header -> 403
    r = await client.post(REFRESH)
    assert r.status_code == 403


async def test_refresh_rotates_and_detects_reuse(client):
    await client.post(SIGNUP, json=USER)
    old_refresh = client.cookies.get("refresh_token")

    # First rotation succeeds and swaps the refresh cookie.
    r1 = await client.post(REFRESH, headers=csrf_header(client))
    assert r1.status_code == 200, r1.text
    new_refresh = client.cookies.get("refresh_token")
    assert new_refresh and new_refresh != old_refresh

    # Replaying the OLD refresh token is reuse -> 401 and sessions revoked.
    client.cookies.set("refresh_token", old_refresh)
    r2 = await client.post(REFRESH, headers={"X-CSRF-Token": client.cookies.get("csrf_token") or ""})
    assert r2.status_code == 401
    assert "reuse" in r2.json()["detail"].lower()


async def test_logout_clears_cookies_and_blocks_me(client):
    await client.post(SIGNUP, json=USER)
    r = await client.post(LOGOUT, headers=csrf_header(client))
    assert r.status_code == 200
    # Access cookie cleared -> /me now unauthorized
    me = await client.get(ME)
    assert me.status_code == 401

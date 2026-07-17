"""Tests for the Google OAuth user-linking logic (without hitting Google).

We exercise `complete_google_login`, which is the part of the callback that upserts
the user, issues a session, and redirects to the SPA — the real token exchange is
Authlib's job and needs live Google credentials.
"""

from app.api.routes.google import complete_google_login
from app.crud import user as user_crud


async def test_google_creates_verified_user_and_redirects(db_session):
    info = {"email": "bob@example.com", "name": "Bob Google", "sub": "google-sub-123"}
    resp = await complete_google_login(db_session, info)

    assert resp.status_code == 302
    assert resp.headers["location"].endswith("/home")
    # Session cookies set on the redirect
    joined = " ".join(
        v.decode() for k, v in resp.raw_headers if k == b"set-cookie"
    )
    assert "access_token=" in joined
    assert "refresh_token=" in joined

    user = await user_crud.get_by_email(db_session, "bob@example.com")
    assert user is not None
    assert user.is_verified is True
    assert user.oauth_provider == "google"
    assert user.hashed_password is None


async def test_google_links_to_existing_email(db_session):
    # Pre-existing password user with the same email.
    existing = await user_crud.create_user(
        db_session, email="carol@example.com", password="password12345", full_name="Carol"
    )
    assert existing.oauth_provider is None

    info = {"email": "carol@example.com", "name": "Carol G", "sub": "google-sub-999"}
    await complete_google_login(db_session, info)

    linked = await user_crud.get_by_email(db_session, "carol@example.com")
    assert linked.oauth_provider == "google"
    assert linked.oauth_sub == "google-sub-999"
    # Original password preserved (account linking, not replacement).
    assert linked.hashed_password is not None

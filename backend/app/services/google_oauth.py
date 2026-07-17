"""Authlib OAuth registry for Google, built lazily so the app runs without creds."""

from functools import lru_cache

from authlib.integrations.starlette_client import OAuth

from app.core.config import settings

GOOGLE_CONF_URL = "https://accounts.google.com/.well-known/openid-configuration"


@lru_cache
def get_oauth() -> OAuth:
    oauth = OAuth()
    oauth.register(
        name="google",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        server_metadata_url=GOOGLE_CONF_URL,
        client_kwargs={"scope": "openid email profile"},
    )
    return oauth

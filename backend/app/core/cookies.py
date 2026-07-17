"""Helpers to set/clear the auth cookies with consistent, safe flags.

- access/refresh: HttpOnly (JS can't read them) -> XSS-safe
- csrf: readable by JS so the SPA can echo it back in the X-CSRF-Token header
"""

from fastapi import Response

from app.core.config import settings


def _common_kwargs() -> dict:
    kwargs: dict = {
        "secure": settings.COOKIE_SECURE,
        "samesite": settings.COOKIE_SAMESITE,
        "path": "/",
    }
    if settings.cookie_domain_or_none:
        kwargs["domain"] = settings.cookie_domain_or_none
    return kwargs


def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
) -> None:
    common = _common_kwargs()
    response.set_cookie(
        settings.ACCESS_COOKIE,
        access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        **common,
    )
    response.set_cookie(
        settings.REFRESH_COOKIE,
        refresh_token,
        httponly=True,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        **common,
    )
    # Not HttpOnly on purpose: the SPA reads it to populate the X-CSRF-Token header.
    response.set_cookie(
        settings.CSRF_COOKIE,
        csrf_token,
        httponly=False,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        **common,
    )


def set_access_cookie(response: Response, access_token: str) -> None:
    response.set_cookie(
        settings.ACCESS_COOKIE,
        access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        **_common_kwargs(),
    )


def clear_auth_cookies(response: Response) -> None:
    common = _common_kwargs()
    common.pop("secure", None)  # delete_cookie takes its own flags
    for name in (settings.ACCESS_COOKIE, settings.REFRESH_COOKIE, settings.CSRF_COOKIE):
        response.delete_cookie(
            name,
            path="/",
            domain=settings.cookie_domain_or_none,
            samesite=settings.COOKIE_SAMESITE,
        )

"""Application settings loaded from environment / .env via pydantic-settings."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Core
    SECRET_KEY: str = "insecure-dev-key-change-me"
    ENVIRONMENT: Literal["dev", "prod", "test"] = "dev"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/appdb"

    # URLs
    FRONTEND_URL: str = "http://localhost:5173"
    BACKEND_URL: str = "http://localhost:8000"

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # Tokens
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ALGORITHM: str = "HS256"

    # Cookies
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"
    COOKIE_DOMAIN: str = ""

    # Cookie names
    ACCESS_COOKIE: str = "access_token"
    REFRESH_COOKIE: str = "refresh_token"
    CSRF_COOKIE: str = "csrf_token"
    CSRF_HEADER: str = "X-CSRF-Token"

    @property
    def google_redirect_uri(self) -> str:
        return f"{self.BACKEND_URL}/auth/google/callback"

    @property
    def google_enabled(self) -> bool:
        return bool(self.GOOGLE_CLIENT_ID and self.GOOGLE_CLIENT_SECRET)

    @property
    def cookie_domain_or_none(self) -> str | None:
        return self.COOKIE_DOMAIN or None


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

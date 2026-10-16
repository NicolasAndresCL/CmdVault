"""Settings del frontend."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    backend_url: str = "http://localhost:8000"
    # La llave viaja solo servidor→servidor: el navegador nunca la ve.
    api_key: str = Field(min_length=16)
    storage_secret: str = Field(min_length=16)
    port: int = 8080
    default_theme: str = "eren"
    page_size: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]

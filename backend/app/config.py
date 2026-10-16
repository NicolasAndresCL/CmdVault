"""Settings tipados desde variables de entorno / ``.env``."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "CmdVault API"
    environment: str = Field(default="development", pattern="^(development|test|production)$")
    # SQLite por defecto para desarrollo sin Docker; en Compose llega la URL de Postgres.
    database_url: str = "sqlite:///./cmdvault.db"
    # Llave para endpoints de escritura. Sin default: falla ruidoso si falta.
    api_key: str = Field(min_length=16)
    seed_on_startup: bool = True
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:8090"])


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]

"""Cliente de API compartido por el proceso (se crea al arrancar, se cierra al apagar)."""

from __future__ import annotations

from app.api_client import ApiClient

_client: ApiClient | None = None


def init(client: ApiClient) -> None:
    global _client
    _client = client


def api() -> ApiClient:
    if _client is None:
        raise RuntimeError("ApiClient no inicializado")
    return _client

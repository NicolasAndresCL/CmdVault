"""Cliente HTTP hacia la API.

Las lecturas **nunca lanzan**: ante un backend caído devuelven vacío y dejan log,
así la UI degrada (mensaje "sin conexión") en vez de romper la página. Las
escrituras devuelven ``(ok, detalle)`` para poder mostrarle el motivo al usuario.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

log = logging.getLogger(__name__)


class ApiClient:
    def __init__(self, base_url: str, api_key: str, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers={"X-API-Key": api_key},
            timeout=10.0,
            transport=transport,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def _get(self, path: str, default: Any, **params: Any) -> Any:
        try:
            r = await self._client.get(path, params={k: v for k, v in params.items() if v not in (None, "")})
            r.raise_for_status()
            return r.json()
        except (httpx.HTTPError, ValueError) as exc:
            log.warning("GET %s falló: %s", path, exc)
            return default

    async def _write(self, method: str, path: str, json: Any = None) -> tuple[bool, Any]:
        try:
            r = await self._client.request(method, path, json=json)
        except httpx.HTTPError as exc:
            log.warning("%s %s falló: %s", method, path, exc)
            return False, "No hay conexión con la API"
        if r.status_code >= 400:
            try:
                body = r.json()
                detail = body.get("detail", body)
            except ValueError:
                detail = r.text
            if isinstance(detail, list):  # errores de validación 422 de FastAPI
                detail = "; ".join(f"{'.'.join(map(str, e.get('loc', [])[1:]))}: {e.get('msg')}" for e in detail)
            return False, detail
        return True, (r.json() if r.content else None)

    # ------------------------------------------------------------ lecturas
    async def healthy(self) -> bool:
        return (await self._get("/healthz", {})).get("status") == "ok"

    async def stats(self) -> dict:
        return await self._get("/api/v1/stats", {})

    async def categories(self) -> list[dict]:
        return await self._get("/api/v1/categories", [])

    async def category(self, slug: str) -> dict | None:
        return await self._get(f"/api/v1/categories/{slug}", None)

    async def facets(self, slug: str) -> dict:
        return await self._get(f"/api/v1/categories/{slug}/facets", {"sections": [], "topics": [], "levels": []})

    async def commands(self, **params: Any) -> dict:
        return await self._get("/api/v1/commands", {"items": [], "total": 0}, **params)

    async def command(self, command_id: int) -> dict | None:
        return await self._get(f"/api/v1/commands/{command_id}", None)

    async def skills(self) -> list[dict]:
        return await self._get("/api/v1/skills", [])

    async def skill(self, slug: str) -> dict | None:
        return await self._get(f"/api/v1/skills/{slug}", None)

    # ------------------------------------------------------------ escrituras
    async def set_favorite(self, command_id: int, value: bool) -> tuple[bool, Any]:
        return await self._write("PUT", f"/api/v1/commands/{command_id}/favorite", {"is_favorite": value})

    async def create_command(self, data: dict) -> tuple[bool, Any]:
        return await self._write("POST", "/api/v1/commands", data)

    async def delete_command(self, command_id: int) -> tuple[bool, Any]:
        return await self._write("DELETE", f"/api/v1/commands/{command_id}")

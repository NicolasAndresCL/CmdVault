"""Punto de entrada del frontend NiceGUI."""

from __future__ import annotations

import logging

from fastapi.responses import JSONResponse
from nicegui import app, ui

from app import (
    pages,  # noqa: F401  (registra las rutas @ui.page)
    state,
)
from app.api_client import ApiClient
from app.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def _startup() -> None:
    s = get_settings()
    state.init(ApiClient(s.backend_url, s.api_key))


async def _shutdown() -> None:
    await state.api().close()


app.on_startup(_startup)
app.on_shutdown(_shutdown)


@app.get("/healthz")
async def healthz() -> JSONResponse:
    """Sano = la UI sirve Y alcanza a la API (si no, 'degraded' con 503)."""
    ok = await state.api().healthy()
    return JSONResponse({"status": "ok" if ok else "degraded", "backend": ok}, status_code=200 if ok else 503)


def main() -> None:
    s = get_settings()
    ui.run(
        title="CmdVault",
        host="0.0.0.0",
        port=s.port,
        favicon="🗝️",
        storage_secret=s.storage_secret,
        reload=False,
        show=False,
        language="es",
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()

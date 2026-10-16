"""Punto de entrada de la API de CmdVault."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import models  # noqa: F401  (registra las tablas en Base.metadata)
from app.api import router, write
from app.config import get_settings
from app.db import Base, get_engine
from app.errors import register_handlers
from app.seed.sync import sync_from_disk

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("cmdvault")


_INIT_LOCK = 0x434D4456  # "CMDV": id del advisory lock de inicialización


def init_db() -> None:
    """Crea el esquema y sincroniza el seed UNA vez aunque arranquen N workers a la vez.

    Cada worker de uvicorn ejecuta el lifespan: sin el lock, con la BD vacía, dos workers
    compiten en ``create_all`` y en los INSERT del seed (violación de unique). El lock es
    transaccional: se libera solo al hacer commit, y el segundo worker ve el seed ya hecho.
    """
    engine = get_engine()
    with engine.begin() as conn:
        if engine.dialect.name == "postgresql":
            conn.execute(text("SELECT pg_advisory_xact_lock(:k)"), {"k": _INIT_LOCK})
        Base.metadata.create_all(conn)
        if get_settings().seed_on_startup:
            with Session(bind=conn) as s:
                sync_from_disk(s)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="1.0.1", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
        allow_headers=["X-API-Key", "Content-Type"],
    )
    register_handlers(app)
    app.include_router(router)
    app.include_router(write)

    @app.get("/healthz", tags=["sistema"])
    def healthz() -> JSONResponse:
        """Sano = la API responde Y la base de datos acepta una consulta."""
        try:
            with get_engine().connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception as exc:  # noqa: BLE001
            log.warning("healthz: BD no disponible: %s", exc)
            return JSONResponse(status_code=503, content={"status": "degraded", "db": "down"})
        return JSONResponse({"status": "ok", "db": "ok"})

    return app


app = create_app()

"""Engine y sesiones de SQLAlchemy 2.x."""

from __future__ import annotations

import json
from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings


class Base(DeclarativeBase):
    pass


@lru_cache
def get_engine() -> Engine:
    url = get_settings().database_url
    # ensure_ascii=False: las tildes de tags/ejemplos quedan legibles y buscables con LIKE.
    kwargs: dict = {"json_serializer": lambda o: json.dumps(o, ensure_ascii=False)}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        if url in {"sqlite://", "sqlite:///:memory:"}:
            kwargs["poolclass"] = StaticPool  # una sola conexión: la BD en memoria sobrevive
        return create_engine(url, **kwargs)
    return create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=10, **kwargs)


@lru_cache
def _session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def new_session() -> Session:
    return _session_factory()()


def get_session() -> Iterator[Session]:
    """Dependencia de FastAPI: una sesión por request."""
    with new_session() as session:
        yield session

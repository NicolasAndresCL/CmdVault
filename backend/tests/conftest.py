"""Fixtures: SQLite en memoria y seed de fixture (independiente del contenido real)."""

from __future__ import annotations

import os
from pathlib import Path

# Antes de importar la app: entorno de test aislado, sin .env ni Postgres.
# TEST_DATABASE_URL permite correr la misma suite contra Postgres real (job test-postgres del CI).
os.environ.update(
    DATABASE_URL=os.environ.get("TEST_DATABASE_URL", "sqlite://"),
    API_KEY="test-api-key-0123456789",
    SEED_ON_STARTUP="false",
    ENVIRONMENT="test",
)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, get_engine, new_session  # noqa: E402
from app.main import app  # noqa: E402
from app.seed.loader import load_seed, load_skills  # noqa: E402
from app.seed.sync import sync  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"
API_KEY = os.environ["API_KEY"]


@pytest.fixture
def bundles():
    return load_seed(FIXTURES / "seed")


@pytest.fixture
def skills():
    return load_skills(FIXTURES / "skills")


@pytest.fixture
def session(bundles, skills):
    engine = get_engine()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with new_session() as s:
        sync(s, bundles, skills)
        yield s


@pytest.fixture
def client(session):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth():
    return {"X-API-Key": API_KEY}

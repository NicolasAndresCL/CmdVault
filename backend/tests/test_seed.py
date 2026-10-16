import json

import pytest
from pydantic import ValidationError

from app.models import Command
from app.seed.loader import DATA_DIR, SKILLS_DIR, load_seed, load_skills
from app.seed.schema import SeedFile
from app.seed.sync import sync


def test_sync_inicial(session):
    assert session.query(Command).count() == 4


def test_sync_idempotente_y_conserva_favoritos(session, bundles, skills):
    cmd = session.query(Command).filter_by(slug="listar-archivos-con-detalle").one()
    cmd.is_favorite = True
    session.commit()
    rep = sync(session, bundles, skills)
    assert (rep.created, rep.updated, rep.removed) == (0, 4, 0)
    session.refresh(cmd)
    assert cmd.is_favorite is True


def test_sync_elimina_seed_retirado_pero_no_los_del_usuario(session, bundles, skills):
    session.add(
        Command(
            category_id=1,
            slug="mio",
            title="Mío",
            command="x",
            section="Común",
            topic="T",
            description="propio",
            examples=[],
            tags=[],
            roadmap=[],
            source="user",
        )
    )
    session.commit()
    bundles["linux"].commands.pop()
    rep = sync(session, bundles, skills)
    assert rep.removed == 1
    assert session.query(Command).filter_by(slug="mio").one()


def test_tags_normalizados(session):
    cmd = session.query(Command).filter_by(slug="listar-archivos-con-detalle").one()
    assert cmd.tags == ["archivos", "listado"]


def test_schema_rechaza_campos_extra():
    with pytest.raises(ValidationError):
        SeedFile.model_validate(
            {
                "category": {
                    "slug": "x",
                    "name": "X",
                    "icon": "i",
                    "description": "descripción",
                    "order": 0,
                    "extra": 1,
                },
                "commands": [],
            }
        )


# ------------------------------------------------------ contenido real versionado


def test_seed_real_es_valido():
    """Toda la biblioteca versionada cumple el contrato (lo mismo que app.seed.validate)."""
    archivos = sorted(DATA_DIR.glob("*.json"))
    assert archivos, "no hay seed en app/seed/data"
    for p in archivos:
        SeedFile.model_validate(json.loads(p.read_text(encoding="utf-8")))
    bundles = load_seed()
    assert {"linux", "python", "windows", "jenkins", "docker", "kubernetes", "terraform", "ansible"} <= set(bundles)


def test_skills_reales_cargan():
    docs = load_skills(SKILLS_DIR)
    assert len(docs) >= 10
    assert all(d.summary and d.content for d in docs)


def test_init_db_crea_esquema_y_seed_idempotente(monkeypatch, bundles, skills):
    """init_db (lo que corre cada worker) se puede ejecutar dos veces seguidas sin duplicar."""
    from app import main
    from app.config import get_settings
    from app.db import Base, get_engine, new_session

    monkeypatch.setattr(main, "sync_from_disk", lambda s: sync(s, bundles, skills))
    monkeypatch.setattr(get_settings(), "seed_on_startup", True)
    Base.metadata.drop_all(get_engine())
    main.init_db()
    main.init_db()
    with new_session() as s:
        assert s.query(Command).count() == 4

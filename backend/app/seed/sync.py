"""Sincronización idempotente del seed versionado con la BD.

- Categorías y skills: upsert por slug.
- Comandos ``source='seed'``: upsert por (categoría, slug del título); se conserva
  ``is_favorite``. Los que desaparecieron de los JSON se eliminan.
- Comandos ``source='user'`` nunca se tocan.
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Category, Command, Skill
from app.schemas import SeedReport
from app.seed.loader import CategoryBundle, SkillDoc, load_seed, load_skills, slugify

log = logging.getLogger(__name__)

_CAMPOS = ("title", "command", "section", "topic", "description", "syntax", "level", "notes")


def sync(s: Session, bundles: dict[str, CategoryBundle], skills: list[SkillDoc]) -> SeedReport:
    created = updated = removed = 0
    for slug, bundle in bundles.items():
        meta = bundle.category
        cat = s.scalar(select(Category).where(Category.slug == slug))
        if cat is None:
            cat = Category(slug=slug)
            s.add(cat)
        cat.name, cat.icon, cat.description, cat.order = meta.name, meta.icon, meta.description, meta.order
        s.flush()

        existentes = {c.slug: c for c in s.scalars(select(Command).where(Command.category_id == cat.id))}
        vistos: set[str] = set()
        for item in bundle.commands:
            cslug = slugify(item.title)
            if cslug in vistos:
                continue  # el validador lo reporta; aquí no se rompe el arranque
            vistos.add(cslug)
            cmd = existentes.get(cslug)
            if cmd is not None and cmd.source == "user":
                continue  # un comando propio con el mismo título gana
            if cmd is None:
                cmd = Command(category_id=cat.id, slug=cslug, source="seed", is_favorite=False)
                s.add(cmd)
                created += 1
            else:
                updated += 1
            for campo in _CAMPOS:
                setattr(cmd, campo, getattr(item, campo))
            cmd.examples = [e.model_dump() for e in item.examples]
            cmd.tags = list(item.tags)
            cmd.roadmap = list(item.roadmap)

        for cslug, cmd in existentes.items():
            if cmd.source == "seed" and cslug not in vistos:
                s.delete(cmd)
                removed += 1

    existentes_sk = {k.slug: k for k in s.scalars(select(Skill))}
    for doc in skills:
        sk = existentes_sk.get(doc.slug) or Skill(slug=doc.slug)
        sk.name, sk.summary, sk.content = doc.name, doc.summary, doc.content
        s.add(sk)
    s.commit()
    report = SeedReport(categories=len(bundles), created=created, updated=updated, removed=removed, skills=len(skills))
    log.info("Seed sincronizado: %s", report.model_dump())
    return report


def sync_from_disk(s: Session) -> SeedReport:
    return sync(s, load_seed(), load_skills())

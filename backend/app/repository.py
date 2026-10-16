"""Acceso a datos. Toda consulta SQL vive aquí; las rutas no tocan el ORM directo."""

from __future__ import annotations

from collections import Counter

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.errors import Conflict, NotFound
from app.models import Category, Command, Skill
from app.schemas import CommandCreate, CommandOut, CommandUpdate, Facet, Facets, Stats
from app.search import ParsedQuery, escape_like
from app.seed.loader import slugify


def to_out(cmd: Command) -> CommandOut:
    data = {c: getattr(cmd, c) for c in CommandOut.model_fields if c != "category"}
    return CommandOut(category=cmd.category.slug, **data)


# ---------------------------------------------------------------- categorías


def list_categories(s: Session) -> list[tuple[Category, int]]:
    stmt = (
        select(Category, func.count(Command.id))
        .outerjoin(Command)
        .group_by(Category.id)
        .order_by(Category.order, Category.name)
    )
    return [(c, n) for c, n in s.execute(stmt).all()]


def get_category(s: Session, slug: str) -> Category:
    cat = s.scalar(select(Category).where(Category.slug == slug))
    if cat is None:
        raise NotFound(f"Categoría '{slug}' no existe")
    return cat


# ---------------------------------------------------------------- comandos


def search_commands(
    s: Session,
    pq: ParsedQuery,
    *,
    category: str | None = None,
    section: str | None = None,
    topic: str | None = None,
    level: str | None = None,
    favorites: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Command], int]:
    stmt = select(Command).join(Category)
    category = category or pq.filters.get("cat")
    if category:
        stmt = stmt.where(Category.slug == category)
    if section:
        stmt = stmt.where(Command.section == section)
    if topic:
        stmt = stmt.where(Command.topic == topic)
    if level or pq.filters.get("level"):
        stmt = stmt.where(func.lower(Command.level) == (level or pq.filters["level"]).lower())
    if favorites:
        stmt = stmt.where(Command.is_favorite.is_(True))
    if f := pq.filters.get("section"):
        stmt = stmt.where(func.lower(Command.section).like(f"%{escape_like(f)}%", escape="\\"))
    if f := pq.filters.get("topic"):
        stmt = stmt.where(func.lower(Command.topic).like(f"%{escape_like(f)}%", escape="\\"))
    if f := pq.filters.get("tag"):
        stmt = stmt.where(func.lower(cast(Command.tags, String)).like(f'%"{escape_like(f)}"%', escape="\\"))
    for term in pq.terms:
        like = f"%{escape_like(term)}%"
        stmt = stmt.where(
            or_(
                func.lower(Command.title).like(like, escape="\\"),
                func.lower(Command.command).like(like, escape="\\"),
                func.lower(Command.description).like(like, escape="\\"),
                func.lower(Command.topic).like(like, escape="\\"),
                func.lower(cast(Command.tags, String)).like(like, escape="\\"),
            )
        )
    total = s.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    stmt = (
        stmt.options(joinedload(Command.category))
        .order_by(Category.order, Command.section, Command.topic, Command.title)
        .limit(limit)
        .offset(offset)
    )
    return list(s.scalars(stmt).unique().all()), total


def get_command(s: Session, command_id: int) -> Command:
    cmd = s.get(Command, command_id, options=[joinedload(Command.category)])
    if cmd is None:
        raise NotFound(f"Comando {command_id} no existe")
    return cmd


def create_command(s: Session, data: CommandCreate) -> Command:
    cat = get_category(s, data.category)
    slug = slugify(data.title)
    if s.scalar(select(Command.id).where(Command.category_id == cat.id, Command.slug == slug)):
        raise Conflict(f"Ya existe un comando '{data.title}' en {cat.name}")
    payload = data.model_dump(exclude={"category"})
    payload["examples"] = [e.model_dump() for e in data.examples]
    payload["tags"] = sorted({t.lower() for t in data.tags})
    cmd = Command(category=cat, slug=slug, source="user", **payload)
    s.add(cmd)
    s.commit()
    return get_command(s, cmd.id)


def _solo_usuario(cmd: Command) -> None:
    if cmd.source == "seed":
        raise Conflict(
            "Los comandos del seed se editan en backend/app/seed/data/*.json (se re-sincronizan al arrancar)"
        )


def update_command(s: Session, command_id: int, data: CommandUpdate) -> Command:
    cmd = get_command(s, command_id)
    _solo_usuario(cmd)
    cambios = data.model_dump(exclude_unset=True)
    if "examples" in cambios and data.examples is not None:
        cambios["examples"] = [e.model_dump() for e in data.examples]
    if "title" in cambios and cambios["title"]:
        cambios["slug"] = slugify(cambios["title"])
    for k, v in cambios.items():
        setattr(cmd, k, v)
    s.commit()
    return get_command(s, command_id)


def delete_command(s: Session, command_id: int) -> None:
    cmd = get_command(s, command_id)
    _solo_usuario(cmd)
    s.delete(cmd)
    s.commit()


def set_favorite(s: Session, command_id: int, value: bool) -> Command:
    cmd = get_command(s, command_id)
    cmd.is_favorite = value
    s.commit()
    return get_command(s, command_id)


def facets(s: Session, category: str) -> Facets:
    cat = get_category(s, category)

    def _agrupar(col) -> list[Facet]:
        rows = s.execute(
            select(col, func.count()).where(Command.category_id == cat.id).group_by(col).order_by(col)
        ).all()
        return [Facet(value=v, total=n) for v, n in rows]

    return Facets(sections=_agrupar(Command.section), topics=_agrupar(Command.topic), levels=_agrupar(Command.level))


def stats(s: Session) -> Stats:
    rows = s.execute(
        select(Command.level, Command.roadmap, Command.examples, Command.is_favorite, Command.source)
    ).all()
    by_level: Counter[str] = Counter()
    by_roadmap: Counter[str] = Counter()
    ejemplos = favs = user = 0
    for level, roadmap, examples, fav, source in rows:
        by_level[level] += 1
        by_roadmap.update(roadmap or [])
        ejemplos += len(examples or [])
        favs += bool(fav)
        user += source == "user"
    return Stats(
        commands=len(rows),
        categories=s.scalar(select(func.count(Category.id))) or 0,
        favorites=favs,
        user_commands=user,
        skills=s.scalar(select(func.count(Skill.id))) or 0,
        examples=ejemplos,
        by_level=dict(by_level),
        by_roadmap=dict(by_roadmap.most_common()),
    )


# ---------------------------------------------------------------- skills


def list_skills(s: Session) -> list[Skill]:
    return list(s.scalars(select(Skill).order_by(Skill.name)).all())


def get_skill(s: Session, slug: str) -> Skill:
    sk = s.scalar(select(Skill).where(Skill.slug == slug))
    if sk is None:
        raise NotFound(f"Skill '{slug}' no existe")
    return sk

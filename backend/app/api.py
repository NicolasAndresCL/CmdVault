"""Rutas HTTP. Solo orquestan: validan entrada, llaman al repositorio y serializan."""

from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, Response, status
from sqlalchemy.orm import Session

from app import repository as repo
from app.config import get_settings
from app.db import get_session
from app.errors import Unauthorized
from app.schemas import (
    CategoryOut,
    CommandCreate,
    CommandOut,
    CommandPage,
    CommandUpdate,
    Facets,
    FavoriteIn,
    SeedReport,
    SkillOut,
    SkillSummary,
    Stats,
)
from app.search import parse_query
from app.seed.sync import sync_from_disk

SessionDep = Annotated[Session, Depends(get_session)]


def require_api_key(x_api_key: Annotated[str | None, Header()] = None) -> None:
    if not x_api_key or not secrets.compare_digest(x_api_key, get_settings().api_key):
        raise Unauthorized("Falta o es inválida la cabecera X-API-Key")


router = APIRouter(prefix="/api/v1")
write = APIRouter(prefix="/api/v1", dependencies=[Depends(require_api_key)])


@router.get("/categories", response_model=list[CategoryOut], tags=["categorías"])
def categories(s: SessionDep) -> list[CategoryOut]:
    return [CategoryOut.model_validate(c).model_copy(update={"total": n}) for c, n in repo.list_categories(s)]


@router.get("/categories/{slug}", response_model=CategoryOut, tags=["categorías"])
def category(slug: str, s: SessionDep) -> CategoryOut:
    cat = repo.get_category(s, slug)
    total = next((n for c, n in repo.list_categories(s) if c.id == cat.id), 0)
    return CategoryOut.model_validate(cat).model_copy(update={"total": total})


@router.get("/categories/{slug}/facets", response_model=Facets, tags=["categorías"])
def category_facets(slug: str, s: SessionDep) -> Facets:
    return repo.facets(s, slug)


@router.get("/commands", response_model=CommandPage, tags=["comandos"])
def commands(
    s: SessionDep,
    q: Annotated[
        str | None, Query(description='Texto libre; admite "frases" y tag:/level:/section:/topic:/cat:')
    ] = None,
    category: str | None = None,
    section: str | None = None,
    topic: str | None = None,
    level: str | None = None,
    favorites: bool = False,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> CommandPage:
    items, total = repo.search_commands(
        s,
        parse_query(q),
        category=category,
        section=section,
        topic=topic,
        level=level,
        favorites=favorites,
        limit=limit,
        offset=offset,
    )
    return CommandPage(items=[repo.to_out(c) for c in items], total=total, limit=limit, offset=offset)


@router.get("/commands/{command_id}", response_model=CommandOut, tags=["comandos"])
def command(command_id: int, s: SessionDep) -> CommandOut:
    return repo.to_out(repo.get_command(s, command_id))


@write.post("/commands", response_model=CommandOut, status_code=status.HTTP_201_CREATED, tags=["comandos"])
def create(data: CommandCreate, s: SessionDep) -> CommandOut:
    return repo.to_out(repo.create_command(s, data))


@write.patch("/commands/{command_id}", response_model=CommandOut, tags=["comandos"])
def update(command_id: int, data: CommandUpdate, s: SessionDep) -> CommandOut:
    return repo.to_out(repo.update_command(s, command_id, data))


@write.delete("/commands/{command_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["comandos"])
def delete(command_id: int, s: SessionDep) -> Response:
    repo.delete_command(s, command_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@write.put("/commands/{command_id}/favorite", response_model=CommandOut, tags=["comandos"])
def favorite(command_id: int, data: FavoriteIn, s: SessionDep) -> CommandOut:
    return repo.to_out(repo.set_favorite(s, command_id, data.is_favorite))


@router.get("/skills", response_model=list[SkillSummary], tags=["skills"])
def skills(s: SessionDep) -> list[SkillSummary]:
    return [SkillSummary.model_validate(k) for k in repo.list_skills(s)]


@router.get("/skills/{slug}", response_model=SkillOut, tags=["skills"])
def skill(slug: str, s: SessionDep) -> SkillOut:
    return SkillOut.model_validate(repo.get_skill(s, slug))


@router.get("/stats", response_model=Stats, tags=["sistema"])
def stats(s: SessionDep) -> Stats:
    return repo.stats(s)


@write.post("/admin/reseed", response_model=SeedReport, tags=["sistema"])
def reseed(s: SessionDep) -> SeedReport:
    return sync_from_disk(s)

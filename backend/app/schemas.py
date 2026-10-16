"""Esquemas de entrada/salida de la API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.seed.schema import ExampleIn, Level, Roadmap


class _Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CategoryOut(_Out):
    slug: str
    name: str
    icon: str
    description: str
    order: int
    total: int = 0


class Example(BaseModel):
    description: str
    code: str


class CommandOut(_Out):
    id: int
    category: str = Field(description="slug de la categoría")
    title: str
    command: str
    section: str
    topic: str
    description: str
    syntax: str | None
    examples: list[Example]
    tags: list[str]
    level: str
    roadmap: list[str]
    notes: str | None
    source: str
    is_favorite: bool
    updated_at: datetime


class CommandPage(BaseModel):
    items: list[CommandOut]
    total: int
    limit: int
    offset: int


class CommandCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    category: str
    title: str = Field(min_length=3, max_length=200)
    command: str = Field(min_length=1)
    section: str = Field(min_length=2, max_length=60)
    topic: str = Field(min_length=2, max_length=80)
    description: str = Field(min_length=10)
    syntax: str | None = None
    examples: list[ExampleIn] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    level: Level = "básico"
    roadmap: list[Roadmap] = Field(default_factory=lambda: ["DevOps"])
    notes: str | None = None


class CommandUpdate(BaseModel):
    """Actualización parcial: solo se aplican los campos enviados."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=3, max_length=200)
    command: str | None = None
    section: str | None = None
    topic: str | None = None
    description: str | None = None
    syntax: str | None = None
    examples: list[ExampleIn] | None = None
    tags: list[str] | None = None
    level: Level | None = None
    roadmap: list[Roadmap] | None = None
    notes: str | None = None


class FavoriteIn(BaseModel):
    is_favorite: bool


class Facet(BaseModel):
    value: str
    total: int


class Facets(BaseModel):
    sections: list[Facet]
    topics: list[Facet]
    levels: list[Facet]


class SkillSummary(_Out):
    slug: str
    name: str
    summary: str


class SkillOut(SkillSummary):
    content: str


class Stats(BaseModel):
    commands: int
    categories: int
    favorites: int
    user_commands: int
    skills: int
    examples: int
    by_level: dict[str, int]
    by_roadmap: dict[str, int]


class SeedReport(BaseModel):
    categories: int
    created: int
    updated: int
    removed: int
    skills: int

"""Contrato de los archivos de seed (``backend/app/seed/data/*.json``).

Es la única fuente de verdad del formato: lo usan el cargador del arranque y el
validador de CI (``python -m app.seed.validate``). Varios archivos pueden compartir
la misma categoría (``linux-redes.json``, ``linux-procesos.json``…): se fusionan por
``category.slug``.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Level = Literal["básico", "intermedio", "avanzado"]
Roadmap = Literal["DevOps", "SRE", "Fullstack", "IA", "Cloud", "Software"]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ExampleIn(_Strict):
    description: str = Field(min_length=3)
    code: str = Field(min_length=1)


class CategoryIn(_Strict):
    slug: str = Field(pattern=r"^[a-z0-9-]+$")
    name: str
    icon: str = Field(description="Nombre de icono Material (p. ej. 'terminal').")
    description: str = Field(min_length=10)
    order: int = Field(ge=0)


class CommandIn(_Strict):
    title: str = Field(min_length=3, max_length=200)
    command: str = Field(min_length=1)
    section: str = Field(min_length=2, max_length=60, description="Subentorno: Ubuntu, AlmaLinux, Django, PowerShell…")
    topic: str = Field(min_length=2, max_length=80, description="Agrupación temática dentro de la categoría.")
    description: str = Field(min_length=20)
    syntax: str | None = None
    examples: list[ExampleIn] = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)
    level: Level = "básico"
    roadmap: list[Roadmap] = Field(min_length=1)
    notes: str | None = None

    @field_validator("tags")
    @classmethod
    def _tags_lower(cls, v: list[str]) -> list[str]:
        return sorted({t.strip().lower() for t in v if t.strip()})


class SeedFile(_Strict):
    category: CategoryIn
    commands: list[CommandIn] = Field(min_length=1)

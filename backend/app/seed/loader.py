"""Lectura y fusión de los archivos de seed (lógica pura, sin BD)."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from app.seed.schema import CategoryIn, CommandIn, SeedFile

DATA_DIR = Path(__file__).resolve().parent / "data"
SKILLS_DIR = Path(__file__).resolve().parent / "skills"


def slugify(texto: str) -> str:
    """'Listar archivos (ls)' -> 'listar-archivos-ls'. Estable: es la clave del upsert."""
    norm = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", norm.lower()).strip("-")


@dataclass
class CategoryBundle:
    category: CategoryIn
    commands: list[CommandIn] = field(default_factory=list)


def load_seed(data_dir: Path = DATA_DIR) -> dict[str, CategoryBundle]:
    """Lee todos los ``*.json`` y los agrupa por slug de categoría."""
    bundles: dict[str, CategoryBundle] = {}
    for path in sorted(data_dir.glob("*.json")):
        seed = SeedFile.model_validate(json.loads(path.read_text(encoding="utf-8")))
        bundle = bundles.setdefault(seed.category.slug, CategoryBundle(seed.category))
        bundle.commands.extend(seed.commands)
    return bundles


@dataclass(frozen=True)
class SkillDoc:
    slug: str
    name: str
    summary: str
    content: str


def parse_frontmatter(front: str) -> dict[str, str]:
    """Frontmatter YAML mínimo: ``clave: valor`` y bloques plegados ``clave: >`` / ``|``."""
    meta: dict[str, str] = {}
    clave: str | None = None
    for line in front.splitlines():
        if clave and (line.startswith((" ", "\t")) or not line.strip()):
            meta[clave] = f"{meta[clave]} {line.strip()}".strip()
            continue
        clave = None
        if ":" in line:
            k, v = line.split(":", 1)
            v = v.strip()
            if v in {">", ">-", "|", "|-"}:
                clave, v = k.strip(), ""
            meta[k.strip()] = v.strip('"')
    return meta


def parse_skill(path: Path) -> SkillDoc:
    """Parsea un SKILL.md con frontmatter ``name``/``description``."""
    raw = path.read_text(encoding="utf-8")
    meta: dict[str, str] = {}
    body = raw
    if raw.startswith("---"):
        _, front, body = raw.split("---", 2)
        meta = parse_frontmatter(front)
    slug = meta.get("name") or path.stem
    titulo = next((ln.lstrip("# ").strip() for ln in body.splitlines() if ln.startswith("# ")), slug)
    return SkillDoc(slug=slugify(slug), name=titulo, summary=meta.get("description", ""), content=body.strip())


def load_skills(skills_dir: Path = SKILLS_DIR) -> list[SkillDoc]:
    return [parse_skill(p) for p in sorted(skills_dir.glob("*.md"))]

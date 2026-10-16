"""Modelos ORM."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _ahora() -> datetime:
    return datetime.now(UTC)


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(80))
    icon: Mapped[str] = mapped_column(String(40))
    description: Mapped[str] = mapped_column(Text)
    order: Mapped[int] = mapped_column(Integer, default=0)

    commands: Mapped[list[Command]] = relationship(back_populates="category", cascade="all, delete-orphan")


class Command(Base):
    __tablename__ = "commands"
    __table_args__ = (UniqueConstraint("category_id", "slug", name="uq_command_category_slug"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), index=True)
    slug: Mapped[str] = mapped_column(String(220))
    title: Mapped[str] = mapped_column(String(200))
    command: Mapped[str] = mapped_column(Text)
    section: Mapped[str] = mapped_column(String(60), index=True)
    topic: Mapped[str] = mapped_column(String(80), index=True)
    description: Mapped[str] = mapped_column(Text)
    syntax: Mapped[str | None] = mapped_column(Text, nullable=True)
    examples: Mapped[list[dict]] = mapped_column(JSON, default=list)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    level: Mapped[str] = mapped_column(String(20), default="básico", index=True)
    roadmap: Mapped[list[str]] = mapped_column(JSON, default=list)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 'seed' = viene de los JSON versionados (se sincroniza en cada arranque); 'user' = creado desde la UI.
    source: Mapped[str] = mapped_column(String(10), default="user", index=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_ahora)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_ahora, onupdate=_ahora)

    category: Mapped[Category] = relationship(back_populates="commands")


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)

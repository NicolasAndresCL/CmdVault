"""Páginas de la aplicación."""

from __future__ import annotations

from nicegui import ui

from app.components import CommandList, command_card
from app.config import get_settings
from app.layout import current_theme_key, frame
from app.state import api
from app.themes import get_theme

ROADMAPS = ["DevOps", "SRE", "Fullstack", "IA", "Cloud", "Software"]
LEVELS = ["básico", "intermedio", "avanzado"]


def _stat(valor: object, etiqueta: str) -> None:
    with ui.card().classes("cv-card p-4 gap-1 min-w-[150px]"):
        ui.label(str(valor)).classes("cv-stat")
        ui.label(etiqueta).classes("cv-muted text-sm")


@ui.page("/")
async def home() -> None:
    async with frame("/"):
        theme = get_theme(current_theme_key())
        with ui.column().classes("gap-1"):
            ui.label("Biblioteca personal de comandos").classes("cv-h1")
            ui.label("Roadmap DevOps · SRE · Arquitecto Fullstack (IA, Cloud, Software). " + theme.tagline).classes(
                "cv-muted"
            )
        stats = await api().stats()
        if stats:
            with ui.row().classes("gap-3 flex-wrap"):
                _stat(stats["commands"], "comandos")
                _stat(stats["examples"], "ejemplos")
                _stat(stats["categories"], "entornos")
                _stat(stats["skills"], "skills de ingeniería")
                _stat(stats["favorites"], "favoritos")
            with ui.row().classes("gap-2 items-center flex-wrap"):
                ui.label("Por roadmap:").classes("cv-muted text-sm")
                for r, n in stats["by_roadmap"].items():
                    ui.chip(f"{r} · {n}", icon="route").props("outline color=primary")
        else:
            with ui.card().classes("cv-card p-4"):
                ui.label("No hay conexión con la API. ¿Está arriba el backend?").classes("text-negative")

        ui.label("Entornos").classes("cv-h2 mt-2")
        with ui.element("div").classes("grid gap-4 w-full grid-cols-1 sm:grid-cols-2 lg:grid-cols-4"):
            for c in await api().categories():
                with (
                    ui.card()
                    .classes("cv-card cv-link-card p-4 gap-2")
                    .on("click", lambda s=c["slug"]: ui.navigate.to(f"/c/{s}"))
                ):
                    with ui.row().classes("items-center gap-2 no-wrap"):
                        ui.icon(c["icon"], size="2rem", color="primary")
                        ui.label(c["name"]).classes("cv-h2")
                    ui.label(c["description"]).classes("cv-muted text-sm")
                    ui.badge(f"{c['total']} comandos").props("color=primary outline")


@ui.page("/c/{slug}")
async def category(slug: str) -> None:
    async with frame(f"/c/{slug}"):
        cat = await api().category(slug)
        if not cat:
            ui.label("Categoría no encontrada").classes("cv-h2")
            return
        with ui.row().classes("items-center gap-3 no-wrap"):
            ui.icon(cat["icon"], size="2.6rem", color="primary")
            with ui.column().classes("gap-0"):
                ui.label(cat["name"]).classes("cv-h1")
                ui.label(cat["description"]).classes("cv-muted")
        facets = await api().facets(slug)
        sections = {"": "Todas"} | {f["value"]: f"{f['value']} ({f['total']})" for f in facets["sections"]}
        topics = {"": "Todos los temas"} | {f["value"]: f"{f['value']} ({f['total']})" for f in facets["topics"]}
        levels = {"": "Todos los niveles"} | {lv: lv for lv in LEVELS}

        with ui.card().classes("cv-card w-full p-3 gap-2"):
            sec = ui.toggle(sections, value="").props("no-caps rounded unelevated toggle-color=primary")
            with ui.row().classes("w-full gap-2 items-center"):
                q = ui.input(placeholder=f"Filtrar dentro de {cat['name']}…").props("dense outlined clearable")
                q.classes("grow")
                top = ui.select(topics, value="").props("dense outlined").classes("w-64")
                lvl = ui.select(levels, value="").props("dense outlined").classes("w-48")

        lista = CommandList(get_settings().page_size, category=slug)

        async def aplicar() -> None:
            lista.filters.update(section=sec.value, topic=top.value, level=lvl.value, q=q.value)
            await lista.reload()

        for el in (sec, top, lvl):
            el.on_value_change(aplicar)
        q.on("keydown.enter", aplicar)
        q.on("clear", aplicar)
        await lista.reload()


@ui.page("/buscar")
async def buscar(q: str = "") -> None:
    async with frame():
        ui.label(f"Resultados para «{q}»" if q else "Buscar").classes("cv-h1")
        ui.label(
            "Tip: combina texto con filtros — tag:redes · level:avanzado · section:ubuntu · cat:kubernetes"
            ' · "frase exacta"'
        ).classes("cv-muted text-sm")
        await CommandList(get_settings().page_size, q=q).reload()


@ui.page("/favoritos")
async def favoritos() -> None:
    async with frame("/favoritos"):
        ui.label("Favoritos").classes("cv-h1")
        await CommandList(get_settings().page_size, favorites=True).reload()


@ui.page("/comando/{command_id}")
async def comando(command_id: int) -> None:
    async with frame():
        cmd = await api().command(command_id)
        if not cmd:
            ui.label("Comando no encontrado").classes("cv-h2")
            return
        ui.link(f"← {cmd['category']}", f"/c/{cmd['category']}").classes("text-primary")
        command_card(cmd, expanded=True)


@ui.page("/skills")
async def skills() -> None:
    async with frame("/skills"):
        ui.label("Mis skills de ingeniería").classes("cv-h1")
        ui.label(
            "Estándares propios probados en producción: el criterio con el que se usan los comandos de esta biblioteca."
        ).classes("cv-muted")
        with ui.element("div").classes("grid gap-4 w-full grid-cols-1 md:grid-cols-2"):
            for sk in await api().skills():
                with (
                    ui.card()
                    .classes("cv-card cv-link-card p-4 gap-2")
                    .on("click", lambda s=sk["slug"]: ui.navigate.to(f"/skills/{s}"))
                ):
                    with ui.row().classes("items-center gap-2 no-wrap"):
                        ui.icon("psychology", color="primary", size="1.6rem")
                        ui.label(sk["name"]).classes("cv-cmd-title")
                    ui.label(sk["summary"]).classes("cv-muted text-sm")


@ui.page("/skills/{slug}")
async def skill(slug: str) -> None:
    async with frame("/skills"):
        sk = await api().skill(slug)
        if not sk:
            ui.label("Skill no encontrada").classes("cv-h2")
            return
        ui.link("← Skills", "/skills").classes("text-primary")
        with ui.card().classes("cv-card w-full p-6"):
            ui.markdown(sk["content"], extras=["fenced-code-blocks", "tables"]).classes("w-full")


@ui.page("/nuevo")
async def nuevo() -> None:
    async with frame("/nuevo"):
        ui.label("Nuevo comando").classes("cv-h1")
        ui.label("Se guarda como comando propio (editable/eliminable). Los del seed se mantienen en los JSON.").classes(
            "cv-muted"
        )
        cats = {c["slug"]: c["name"] for c in await api().categories()}
        ejemplos: list[dict[str, ui.input | ui.textarea]] = []
        with ui.card().classes("cv-card w-full p-5 gap-3"):
            with ui.row().classes("w-full gap-3"):
                f_cat = ui.select(cats, label="Categoría", value=next(iter(cats), None)).classes("w-56")
                f_sec = ui.input("Sección (p. ej. Ubuntu, Django, PowerShell)").classes("grow")
                f_top = ui.input("Tema (p. ej. Redes)").classes("grow")
            f_title = ui.input("Título").classes("w-full")
            f_cmd = ui.textarea("Comando").props("autogrow").classes("w-full font-mono")
            f_desc = ui.textarea("Descripción").props("autogrow").classes("w-full")
            f_syn = ui.input("Sintaxis (opcional)").classes("w-full font-mono")
            with ui.row().classes("w-full gap-3"):
                f_lvl = ui.select(LEVELS, label="Nivel", value="básico").classes("w-48")
                f_road = (
                    ui.select(ROADMAPS, label="Roadmap", value=["DevOps"], multiple=True)
                    .props("use-chips")
                    .classes("grow")
                )
                f_tags = ui.input("Tags separados por coma").classes("grow")
            f_notes = ui.textarea("Notas / trampas (opcional, admite Markdown)").props("autogrow").classes("w-full")
            ui.label("Ejemplos").classes("cv-h2")
            box = ui.column().classes("w-full gap-2")

            def add_example() -> None:
                with box, ui.card().classes("w-full p-3 gap-1 cv-card"):
                    d = ui.input("Descripción del ejemplo").classes("w-full")
                    c = ui.textarea("Código").props("autogrow").classes("w-full font-mono")
                ejemplos.append({"description": d, "code": c})

            add_example()
            ui.button("Agregar ejemplo", icon="add", on_click=add_example).props("outline color=primary")

            async def guardar() -> None:
                data = {
                    "category": f_cat.value,
                    "title": f_title.value,
                    "command": f_cmd.value,
                    "section": f_sec.value,
                    "topic": f_top.value,
                    "description": f_desc.value,
                    "syntax": f_syn.value or None,
                    "level": f_lvl.value,
                    "roadmap": f_road.value or ["DevOps"],
                    "tags": [t.strip() for t in (f_tags.value or "").split(",") if t.strip()],
                    "notes": f_notes.value or None,
                    "examples": [
                        {"description": e["description"].value, "code": e["code"].value}
                        for e in ejemplos
                        if e["code"].value
                    ],
                }
                ok, res = await api().create_command(data)
                if ok:
                    ui.notify("Comando guardado", type="positive")
                    ui.navigate.to(f"/comando/{res['id']}")
                else:
                    ui.notify(f"No se pudo guardar: {res}", type="negative", multi_line=True, timeout=6000)

            ui.button("Guardar", icon="save", on_click=guardar).props("color=primary unelevated")

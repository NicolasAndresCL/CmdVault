"""Componentes reutilizables de UI."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from nicegui import ui

from app.langs import guess_language
from app.state import api

LEVEL_COLOR = {"básico": "positive", "intermedio": "warning", "avanzado": "negative"}


def copy_button(text: str) -> None:
    async def _copy() -> None:
        ui.clipboard.write(text)
        ui.notify("Copiado al portapapeles", type="positive", position="bottom-right", timeout=1200)

    ui.button(icon="content_copy", on_click=_copy).props("flat round dense size=sm color=primary").tooltip("Copiar")


def command_card(cmd: dict, on_deleted: Callable[[], Awaitable[None]] | None = None, expanded: bool = False) -> None:
    cat, section = cmd["category"], cmd["section"]
    with ui.card().classes("cv-card w-full gap-2 p-4"):
        with ui.row().classes("w-full items-start no-wrap gap-2"):
            with ui.column().classes("grow gap-1 min-w-0"):
                ui.label(cmd["title"]).classes("cv-cmd-title")
                with ui.row().classes("gap-1 items-center"):
                    ui.badge(section).props("color=primary")
                    ui.badge(cmd["topic"]).props("color=secondary text-color=dark outline")
                    ui.badge(cmd["level"]).props(f"color={LEVEL_COLOR.get(cmd['level'], 'info')} outline")
                    if cmd["source"] == "user":
                        ui.badge("propio").props("color=accent")
            _favorite_button(cmd)
        with ui.row().classes("w-full items-start no-wrap gap-1"):
            ui.label(cmd["command"]).classes("cv-cmd grow")
            copy_button(cmd["command"])
        ui.label(cmd["description"]).classes("cv-muted text-sm")

        exp = (
            ui.expansion(f"Ejemplos ({len(cmd['examples'])}) y detalle", icon="code", value=False)
            .classes("w-full")
            .props("dense header-class=text-primary")
        )
        cargado = {"ok": False}

        def _fill() -> None:
            # Se construye al abrir: evita montar cientos de bloques de código que no se miran.
            if cargado["ok"]:
                return
            cargado["ok"] = True
            with exp:
                if cmd.get("syntax"):
                    ui.label("Sintaxis").classes("text-xs uppercase cv-muted")
                    ui.code(cmd["syntax"], language=guess_language(cat, section, cmd["syntax"])).classes("w-full")
                for ex in cmd["examples"]:
                    ui.label(ex["description"]).classes("text-sm font-semibold mt-2")
                    ui.code(ex["code"], language=guess_language(cat, section, ex["code"])).classes("w-full")
                if cmd.get("notes"):
                    with ui.row().classes("cv-note w-full items-start no-wrap mt-2"):
                        ui.icon("lightbulb", color="accent")
                        ui.markdown(cmd["notes"]).classes("text-sm")
                with ui.row().classes("gap-1 mt-2 items-center"):
                    for t in cmd["tags"]:
                        ui.chip(t, icon="sell").props("dense outline color=primary").on(
                            "click", lambda t=t: ui.navigate.to(f"/buscar?q=tag:{t}")
                        )
                    for r in cmd["roadmap"]:
                        ui.chip(r, icon="route").props("dense color=secondary text-color=dark")
                    ui.space()
                    ui.link("Ver ficha", f"/comando/{cmd['id']}").classes("text-primary text-sm")
                    if cmd["source"] == "user" and on_deleted:
                        ui.button(icon="delete", on_click=lambda: _delete(cmd, on_deleted)).props(
                            "flat round dense color=negative"
                        ).tooltip("Eliminar comando propio")

        exp.on_value_change(lambda e: _fill() if e.value else None)
        if expanded:
            exp.value = True


def _favorite_button(cmd: dict) -> None:
    def _icon() -> str:
        return "star" if cmd["is_favorite"] else "star_border"

    async def _toggle() -> None:
        ok, data = await api().set_favorite(cmd["id"], not cmd["is_favorite"])
        if not ok:
            ui.notify(f"No se pudo actualizar: {data}", type="negative")
            return
        cmd["is_favorite"] = data["is_favorite"]
        btn.props(f"icon={_icon()}")

    btn = ui.button(icon=_icon(), on_click=_toggle).props("flat round color=accent").tooltip("Favorito")


async def _delete(cmd: dict, on_deleted: Callable[[], Awaitable[None]]) -> None:
    ok, data = await api().delete_command(cmd["id"])
    if ok:
        ui.notify("Comando eliminado", type="positive")
        await on_deleted()
    else:
        ui.notify(f"No se pudo eliminar: {data}", type="negative")


class CommandList:
    """Lista paginada ("Cargar más") sobre ``/api/v1/commands`` con filtros mutables."""

    def __init__(self, page_size: int, **filters: object) -> None:
        self.page_size = page_size
        self.filters: dict[str, object] = dict(filters)
        self.offset = 0
        self.header = ui.label().classes("cv-muted text-sm")
        self.container = ui.column().classes("w-full gap-3")
        self.more = ui.button("Cargar más", icon="expand_more", on_click=self._load_more).props("outline color=primary")

    async def reload(self) -> None:
        self.offset = 0
        self.container.clear()
        await self._fetch()

    async def _load_more(self) -> None:
        self.offset += self.page_size
        await self._fetch()

    async def _fetch(self) -> None:
        page = await api().commands(**self.filters, limit=self.page_size, offset=self.offset)
        total = page.get("total", 0)
        self.header.text = f"{total} comando{'s' if total != 1 else ''}"
        with self.container:
            if not page["items"] and self.offset == 0:
                with ui.column().classes("w-full items-center py-10 cv-muted"):
                    ui.icon("search_off", size="3rem")
                    ui.label("Sin resultados")
            for cmd in page["items"]:
                command_card(cmd, on_deleted=self.reload)
        self.more.set_visibility(self.offset + self.page_size < total)

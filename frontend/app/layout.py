"""Marco común de todas las páginas: tema, cabecera, menú lateral."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from nicegui import app, ui

from app.state import api
from app.themes import THEMES, css_variables, get_theme

FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link href="https://fonts.googleapis.com/css2?family=Bangers&family=Cinzel:wght@600;800'
    '&family=Inter:wght@400;600;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">'
)

BASE_CSS = """
body { background: var(--cv-bg); background-image: var(--cv-bg-image); background-attachment: fixed;
       color: var(--cv-text); font-family: 'Inter', system-ui, sans-serif; }
.q-header { background: color-mix(in srgb, var(--cv-surface) 82%, transparent) !important;
            backdrop-filter: blur(10px); border-bottom: 1px solid var(--cv-border); color: var(--cv-text); }
.q-drawer { background: var(--cv-surface) !important; border-right: 1px solid var(--cv-border); }
.cv-brand { font-family: var(--cv-heading); font-size: 1.6rem; letter-spacing: .04em; color: var(--q-primary); }
.cv-h1 { font-family: var(--cv-heading); font-size: 2.2rem; line-height: 1.1; letter-spacing: .02em; }
.cv-h2 { font-family: var(--cv-heading); font-size: 1.35rem; letter-spacing: .02em; }
.cv-muted { color: var(--cv-muted); }
.cv-card { background: var(--cv-surface) !important; border: 1px solid var(--cv-border); border-radius: 14px;
           color: var(--cv-text); box-shadow: none; transition: box-shadow .2s, transform .2s, border-color .2s; }
.cv-card:hover { box-shadow: 0 0 0 1px var(--q-primary), 0 10px 30px var(--cv-glow); }
.cv-link-card { cursor: pointer; }
.cv-link-card:hover { transform: translateY(-2px); }
.cv-stat { font-family: var(--cv-heading); font-size: 2rem; color: var(--q-primary); line-height: 1; }
.cv-cmd { font-family: 'JetBrains Mono', ui-monospace, monospace; background: var(--cv-code-bg); color: var(--cv-code-text);
          border-radius: 8px; padding: .45rem .7rem; white-space: pre-wrap; word-break: break-word;
          border: 1px solid var(--cv-border); font-size: .88rem; }
.cv-cmd-title { font-weight: 700; font-size: 1.02rem; }
.cv-note { border-left: 3px solid var(--q-accent); background: var(--cv-surface-2); padding: .5rem .8rem;
           border-radius: 6px; }
.nicegui-code { background: var(--cv-code-bg) !important; border: 1px solid var(--cv-border); border-radius: 8px; }
.nicegui-code .codehilite, .nicegui-code pre { background: transparent !important; color: var(--cv-code-text); }
.body--dark .nicegui-code .codehilite pre span { filter: brightness(1.35) saturate(1.1); }
.nicegui-markdown pre { background: var(--cv-code-bg); color: var(--cv-code-text); padding: .6rem; border-radius: 8px; }
.nicegui-markdown code { font-family: 'JetBrains Mono', monospace; }
.nicegui-markdown table { border-collapse: collapse; }
.nicegui-markdown th, .nicegui-markdown td { border: 1px solid var(--cv-border); padding: .3rem .6rem; }
.nicegui-markdown a { color: var(--q-primary); }
.q-field__native, .q-field__label, .q-item, .q-expansion-item { color: var(--cv-text); }
.q-menu { background: var(--cv-surface); color: var(--cv-text); }
"""

NAV_FIJA = [
    ("Inicio", "home", "/"),
    ("Favoritos", "star", "/favoritos"),
    ("Mis skills de ingeniería", "psychology", "/skills"),
    ("Nuevo comando", "add_circle", "/nuevo"),
]


def current_theme_key() -> str:
    from app.config import get_settings

    return app.storage.user.get("theme", get_settings().default_theme)


def _apply_theme() -> None:
    theme = get_theme(current_theme_key())
    ui.add_head_html(FONTS)
    ui.add_css(BASE_CSS + css_variables(theme))
    ui.colors(**theme.quasar)
    ui.dark_mode(theme.dark)


def _set_theme(key: str) -> None:
    app.storage.user["theme"] = key
    ui.navigate.reload()


def _go_search(q: str) -> None:
    if q.strip():
        ui.navigate.to(f"/buscar?q={q.strip()}")


@asynccontextmanager
async def frame(active: str = "") -> AsyncIterator[ui.column]:
    _apply_theme()
    cats = await api().categories()

    with ui.header().classes("items-center gap-3 px-4 py-2"):
        ui.button(icon="menu", on_click=lambda: drawer.toggle()).props("flat round color=primary")
        with ui.link(target="/").classes("no-underline"):
            ui.label("CmdVault").classes("cv-brand")
        ui.space()
        search = (
            ui.input(placeholder='Buscar… (tag:redes level:avanzado cat:docker "frase")')
            .props("dense outlined rounded clearable")
            .classes("w-[28rem] max-w-[50vw]")
        )
        with search.add_slot("prepend"):
            ui.icon("search")
        search.on("keydown.enter", lambda: _go_search(search.value or ""))
        ui.select(
            {k: t.label for k, t in THEMES.items()},
            value=current_theme_key(),
            on_change=lambda e: _set_theme(e.value),
        ).props("dense outlined options-dense").classes("w-56").tooltip("Tema")

    with ui.left_drawer(value=True).props("width=260 bordered") as drawer, ui.column().classes("w-full gap-0"):
        for label, icon, href in NAV_FIJA:
            _nav_item(label, icon, href, active == href)
        ui.separator().classes("my-2")
        ui.label("Biblioteca").classes("text-xs uppercase cv-muted px-4 pb-1")
        if not cats:
            ui.label("Sin conexión con la API").classes("text-negative px-4")
        for c in cats:
            href = f"/c/{c['slug']}"
            _nav_item(f"{c['name']}", c["icon"], href, active == href, badge=c["total"])

    with ui.column().classes("w-full max-w-6xl mx-auto p-4 gap-4") as content:
        yield content


def _nav_item(label: str, icon: str, href: str, active: bool, badge: int | None = None) -> None:
    with (
        ui.item(on_click=lambda h=href: ui.navigate.to(h))
        .classes("rounded-lg mx-2")
        .props("clickable" + (" active active-class=text-primary" if active else ""))
    ):
        with ui.item_section().props("avatar"):
            ui.icon(icon, color="primary" if active else None)
        with ui.item_section():
            ui.item_label(label)
        if badge is not None:
            with ui.item_section().props("side"):
                ui.badge(str(badge)).props("color=primary outline")

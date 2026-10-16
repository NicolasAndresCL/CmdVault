"""Temas visuales (datos puros). Cada tema define la paleta Quasar y variables CSS propias."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    key: str
    label: str
    dark: bool
    quasar: dict[str, str]  # primary/secondary/accent/positive/negative/info/warning
    css: dict[str, str]  # variables --cv-*
    heading_font: str
    tagline: str


THEMES: dict[str, Theme] = {
    "dark": Theme(
        key="dark",
        label="Dark",
        dark=True,
        quasar={
            "primary": "#4f8cff",
            "secondary": "#8b5cf6",
            "accent": "#22d3ee",
            "positive": "#22c55e",
            "negative": "#ef4444",
            "info": "#38bdf8",
            "warning": "#f59e0b",
        },
        css={
            "bg": "#0e1015",
            "bg-image": "radial-gradient(1200px 600px at 10% -10%, #1b2440 0%, transparent 60%)",
            "surface": "#161a22",
            "surface-2": "#1d2230",
            "border": "#2a3142",
            "text": "#e6e8ee",
            "muted": "#9aa3b5",
            "code-bg": "#0b0d12",
            "code-text": "#e6e8ee",
            "glow": "rgba(79, 140, 255, .25)",
        },
        heading_font="'Inter', system-ui, sans-serif",
        tagline="Modo noche: foco total en la terminal.",
    ),
    "luffy": Theme(
        key="luffy",
        label="Luffy · Quinta Marcha",
        dark=False,
        # Gear 5 / Nika: blanco nube, morado del cielo, rojo del chaleco y dorado del sombrero.
        quasar={
            "primary": "#7c4dff",
            "secondary": "#e63946",
            "accent": "#ffbe0b",
            "positive": "#2ec4b6",
            "negative": "#e63946",
            "info": "#9d7bff",
            "warning": "#ffbe0b",
        },
        css={
            "bg": "#fbf8ff",
            "bg-image": (
                "radial-gradient(900px 420px at 85% -5%, #ffe8a3 0%, transparent 55%),"
                "radial-gradient(800px 500px at 0% 0%, #e9ddff 0%, transparent 60%),"
                "radial-gradient(600px 400px at 50% 110%, #ffffff 0%, transparent 70%)"
            ),
            "surface": "#ffffff",
            "surface-2": "#f4eeff",
            "border": "#e2d6ff",
            "text": "#2a1f3d",
            "muted": "#6b5d85",
            "code-bg": "#f6f1ff",
            "code-text": "#2a1f3d",
            "glow": "rgba(124, 77, 255, .28)",
        },
        heading_font="'Bangers', 'Inter', sans-serif",
        tagline="¡Libertad! El ritmo del tambor de la liberación.",
    ),
    "eren": Theme(
        key="eren",
        label="Eren · Titán Fundador",
        dark=True,
        # El Retumbar: hueso, cielo color brasa, tierra quemada y óxido.
        quasar={
            "primary": "#d9622b",
            "secondary": "#e8dcc4",
            "accent": "#a33a1f",
            "positive": "#7fa36b",
            "negative": "#c0392b",
            "info": "#c9a27a",
            "warning": "#e0a43a",
        },
        css={
            "bg": "#130d0a",
            "bg-image": (
                "radial-gradient(1100px 520px at 50% -15%, #5a2410 0%, transparent 60%),"
                "linear-gradient(180deg, #1c120d 0%, #130d0a 70%)"
            ),
            "surface": "#1f1611",
            "surface-2": "#2a1d16",
            "border": "#3d2a1f",
            "text": "#efe6d6",
            "muted": "#b8a58c",
            "code-bg": "#0d0907",
            "code-text": "#f1ece4",
            "glow": "rgba(217, 98, 43, .30)",
        },
        heading_font="'Cinzel', Georgia, serif",
        tagline="Sigue avanzando hasta destruir a tus enemigos… o tus bugs.",
    ),
}

DEFAULT_THEME = "eren"


def get_theme(key: str | None) -> Theme:
    return THEMES.get(key or "", THEMES[DEFAULT_THEME])


def css_variables(theme: Theme) -> str:
    vars_ = "".join(f"--cv-{k}:{v};" for k, v in theme.css.items())
    return f":root{{{vars_}--cv-heading:{theme.heading_font};}}"

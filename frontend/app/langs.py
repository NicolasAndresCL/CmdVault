"""Elige el lexer de Pygments para resaltar cada bloque (lógica pura)."""

from __future__ import annotations

import re

_CLI_PY = re.compile(
    r"^\s*(\$ )?(python3?|py|pip3?|uv|uvx|pipx|django-admin|\./manage\.py|manage\.py|uvicorn|gunicorn|fastapi|"
    r"pytest|alembic|ruff|mypy|black|coverage|poetry|celery)\b",
    re.MULTILINE,
)


def guess_language(category: str, section: str, code: str) -> str:
    c = code.lstrip()
    if c.startswith(("FROM ", "# syntax=")) or "\nFROM " in code:
        return "docker"
    if category == "windows":
        return "powershell" if section.lower() == "powershell" else "batch"
    if category == "python":
        return "bash" if _CLI_PY.match(code) else "python"
    if category == "jenkins":
        return (
            "groovy"
            if re.search(r"^\s*(pipeline|node|stage|def |@Library|steps|post|Jenkins\.)", code, re.M)
            else "bash"
        )
    if category == "terraform":
        return (
            "bash"
            if re.match(r"^\s*(\$ )?(terraform|tofu|tflint|checkov|trivy|infracost|terraform-docs|export|TF_)", code)
            else "terraform"
        )
    if category in {"kubernetes", "ansible", "docker"} and re.match(
        r"^\s*(---|apiVersion:|- name:|- hosts:|services:|[a-z_]+:\s*$)", code
    ):
        return "yaml"
    return "bash"

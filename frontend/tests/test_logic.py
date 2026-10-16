import re

import pytest

from app.langs import guess_language
from app.themes import DEFAULT_THEME, THEMES, css_variables, get_theme

HEX = re.compile(r"^#[0-9a-f]{6}$", re.I)


def test_hay_tres_temas_y_default():
    assert set(THEMES) == {"dark", "luffy", "eren"}
    assert get_theme("no-existe").key == DEFAULT_THEME


@pytest.mark.parametrize("theme", THEMES.values(), ids=lambda t: t.key)
def test_paletas_completas(theme):
    assert {"primary", "secondary", "accent", "positive", "negative", "info", "warning"} <= set(theme.quasar)
    assert all(HEX.match(v) for v in theme.quasar.values())
    assert {"bg", "surface", "text", "muted", "code-bg", "code-text", "border"} <= set(theme.css)
    assert "--cv-heading" in css_variables(theme)


def test_solo_luffy_es_claro():
    assert [t.key for t in THEMES.values() if not t.dark] == ["luffy"]


@pytest.mark.parametrize(
    ("cat", "section", "code", "lang"),
    [
        ("windows", "PowerShell", "Get-Process", "powershell"),
        ("windows", "CMD", "dir /s", "batch"),
        ("python", "Django", "python manage.py migrate", "bash"),
        ("python", "FastAPI", "@app.get('/')\ndef root(): ...", "python"),
        ("jenkins", "Pipeline", "pipeline {\n agent any\n}", "groovy"),
        ("jenkins", "CLI", "java -jar jenkins-cli.jar list-jobs", "bash"),
        ("terraform", "HCL", 'resource "aws_s3_bucket" "b" {}', "terraform"),
        ("terraform", "Flujo básico", "terraform plan -out tf.plan", "bash"),
        ("kubernetes", "Workloads", "apiVersion: apps/v1\nkind: Deployment", "yaml"),
        ("ansible", "Playbooks", "- hosts: web\n  tasks: []", "yaml"),
        ("docker", "Build y registro", "FROM python:3.13-slim\nUSER app", "docker"),
        ("linux", "Ubuntu", "sudo apt update", "bash"),
        ("postgres", "Consultas y esquema", "SELECT pg_size_pretty(pg_database_size('app'));", "sql"),
        ("postgres", "psql y conexión", "psql -h localhost -U app -d app", "bash"),
        ("mysql", "Usuarios y permisos", "GRANT SELECT ON app.* TO 'lector'@'%';", "sql"),
        ("mongodb", "CRUD y consultas", "db.users.find({ activo: true })", "javascript"),
        ("mongodb", "mongosh y conexión", "mongosh 'mongodb://localhost:27017'", "bash"),
        ("web", "Nginx", "server {\n  listen 80;\n}", "nginx"),
        ("web", "Apache", "<VirtualHost *:80>\n</VirtualHost>", "apacheconf"),
        ("web", "TLS y certificados", "sudo certbot --nginx -d ejemplo.cl", "bash"),
        ("claude", "SDK Python", "import anthropic\nclient = anthropic.Anthropic()", "python"),
        ("claude", "API con curl", "curl -s https://api.anthropic.com/v1/models", "bash"),
        ("vps", "Despliegue", "services:\n  web:\n    image: nginx", "yaml"),
        ("git", "Día a día", "git status -sb", "bash"),
    ],
)
def test_guess_language(cat, section, code, lang):
    assert guess_language(cat, section, code) == lang


def test_settings_y_estado():
    from app import state
    from app.api_client import ApiClient
    from app.config import get_settings

    s = get_settings()
    assert s.backend_url.startswith("http") and s.page_size > 0
    with pytest.raises(RuntimeError):
        state.api()
    c = ApiClient(s.backend_url, s.api_key)
    state.init(c)
    assert state.api() is c

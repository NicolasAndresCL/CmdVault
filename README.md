# CmdVault

[![CI](https://github.com/NicolasAndresCL/CmdVault/actions/workflows/ci.yml/badge.svg)](https://github.com/NicolasAndresCL/CmdVault/actions/workflows/ci.yml)

Biblioteca personal de comandos para un roadmap **DevOps → SRE → Arquitecto Fullstack (IA, Cloud, Software)**.
Cada comando trae descripción, sintaxis, ejemplos de uso común, notas con trampas reales, nivel, tags y roadmap.
Incluye además mis **skills de ingeniería** (estándares propios) como documentación navegable.

| Entorno | Secciones | Comandos |
|---|---|---|
| Linux | Común · Ubuntu · AlmaLinux | 143 |
| Python | Python · Django · DRF · FastAPI | 115 |
| Windows | CMD · PowerShell | 108 |
| Jenkins | Pipeline · CLI · Docker · Administración | 66 |
| Docker | Imágenes · Contenedores · Compose · Redes y volúmenes · Build y registro · Sistema y diagnóstico | 121 |
| Kubernetes | kubectl básico · Workloads · Redes y servicios · Configuración y secretos · Troubleshooting · Helm · Clúster y contexto | 116 |
| Terraform | Flujo básico · Estado · Módulos y workspaces · HCL · Calidad y CI | 79 |
| Ansible | Ad-hoc · Playbooks · Inventario · Roles y Galaxy · Vault y secretos · Calidad y depuración | 78 |
| **Total** | | **826 comandos · 2.090 ejemplos · 11 skills** |

## Arquitectura

```
┌──────────────┐  httpx + X-API-Key  ┌──────────────┐   SQLAlchemy 2   ┌──────────────┐
│  frontend    │ ──────────────────▶ │   backend    │ ───────────────▶ │  PostgreSQL  │
│  NiceGUI 3   │                     │  FastAPI     │                  │  18-alpine   │
│  :8090       │                     │  :8000       │ ◀── seed JSON    │  volumen     │
└──────────────┘                     └──────────────┘   (al arrancar)  └──────────────┘
```

- **backend/** — FastAPI por capas: `config` (pydantic-settings) → `db` → `models` → `repository` (todo el SQL)
  → `api` (rutas finas). Lógica pura aislada en `search.py` y `seed/loader.py`. Excepciones de dominio
  (`errors.py`) que viajan como HTTP con un único handler.
- **Seed versionado**: la biblioteca vive en `backend/app/seed/data/*.json`, validada por un contrato pydantic
  (`seed/schema.py`, `extra="forbid"`). Al arrancar se sincroniza de forma **idempotente**: upsert por
  (categoría, slug del título), conserva favoritos, elimina lo retirado y **nunca toca los comandos propios**
  creados desde la UI.
- **frontend/** — NiceGUI con tres temas (**Dark**, **Luffy · Quinta Marcha**, **Eren · Titán Fundador**)
  guardados por usuario. El cliente HTTP **nunca lanza** en lecturas: si la API cae, la UI degrada con un aviso.
  La API key viaja solo servidor→servidor; el navegador no la ve.

## Arranque rápido (Docker)

```powershell
Copy-Item .env.example .env      # y reemplazar los secretos
docker compose up -d --build --wait
./scripts/smoke.sh               # (Git Bash) healthchecks + render de todas las páginas
```

- UI: <http://localhost:8090> · API + Swagger: <http://localhost:8000/docs>
- El 8090 es a propósito: el 8080 lo usa el controller Jenkins local. Se cambia con `FRONTEND_PORT` en `.env`.
- `docker compose down` conserva los datos; **`down -v` borra el volumen de Postgres** (favoritos y comandos propios).

Respaldo del volumen de Postgres:

```powershell
docker compose exec db pg_dump -U cmdvault cmdvault > backup_cmdvault.sql
```

## Desarrollo sin Docker

```powershell
python -m venv env; env\Scripts\activate
pip install -r backend\requirements-dev.txt -r frontend\requirements-dev.txt

# backend (SQLite por defecto)
cd backend; $env:API_KEY="dev-key-0123456789abc"; uvicorn app.main:app --reload --port 8000

# frontend (otra terminal)
cd frontend; $env:API_KEY="dev-key-0123456789abc"; $env:STORAGE_SECRET="dev-secret-0123456789"; $env:PORT="8090"
python -m app.main
```

## Buscador

La barra superior acepta texto libre, frases entre comillas y filtros combinables:

```
tag:redes level:avanzado          cat:kubernetes "rollout"          section:almalinux firewall
```

## API

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/healthz` | 200 si API **y** BD responden; 503 `degraded` si no |
| GET | `/api/v1/categories` · `/{slug}` · `/{slug}/facets` | Entornos con totales; secciones/temas/niveles |
| GET | `/api/v1/commands?q=&category=&section=&topic=&level=&favorites=&limit=&offset=` | Búsqueda paginada |
| GET | `/api/v1/commands/{id}` | Ficha de un comando |
| POST · PATCH · DELETE | `/api/v1/commands[/{id}]` | Comandos propios (requiere `X-API-Key`) |
| PUT | `/api/v1/commands/{id}/favorite` | Marcar favorito (requiere `X-API-Key`) |
| GET | `/api/v1/skills` · `/{slug}` | Skills de ingeniería |
| GET | `/api/v1/stats` | Totales por nivel y roadmap |
| POST | `/api/v1/admin/reseed` | Re-sincroniza el seed sin reiniciar (requiere `X-API-Key`) |

Los comandos del seed devuelven **409** si se intentan editar o borrar por API: se editan en el JSON.

## Agregar contenido

1. Editar o crear `backend/app/seed/data/<categoria>-<tema>.json` siguiendo `seed/schema.py`
   (ejemplo en `seed/ejemplo.json.txt`).
2. Validar: `cd backend; python -m app.seed.validate` (detecta campos extra y títulos duplicados).
3. `docker compose up -d --build backend` — el arranque sincroniza.

Las skills se copian desde `~/.claude/skills/*/SKILL.md` a `backend/app/seed/skills/`.

## Calidad

| Suite | Tests | Cobertura | Umbral CI |
|---|---|---|---|
| backend (SQLite y Postgres 18) | 30 | 97 % | 90 % |
| frontend (lógica + cliente HTTP) | 23 | 89 % | 80 % |

Reproducir **todo** el CI en local antes de commitear (Git Bash):

```bash
./scripts/verificar.sh              # lint + seed + tests SQLite/Postgres 18 + frontend + hadolint + build + smoke
./scripts/verificar.sh --sin-docker # solo lint y tests
```

CI (`.github/workflows/ci.yml`), en cascada rápido → lento: **lint** (ruff + formato + contrato del seed) →
**tests** backend SQLite · backend Postgres 18 · frontend → **build** (`docker compose up --wait` + `smoke.sh`).
Permisos `contents: read`, Dependabot semanal (pip, Docker, Compose, Actions).

## Stack

Python 3.14 · FastAPI 0.143 · SQLAlchemy 2.1 · psycopg 3 · Pydantic 2 · NiceGUI 3.18 · PostgreSQL 18 ·
Docker multi-stage no-root con healthchecks · GitHub Actions.

---
Autor: **Nicolás Andrés Cano Leal**

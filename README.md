# CmdVault — biblioteca personal de comandos DevOps · SRE · Fullstack

[![CI](https://github.com/NicolasAndresCL/CmdVault/actions/workflows/ci.yml/badge.svg)](https://github.com/NicolasAndresCL/CmdVault/actions/workflows/ci.yml)
![Versión](https://img.shields.io/badge/versi%C3%B3n-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.14-3776AB)

| | |
|---|---|
| **Versión** | 1.0.0 |
| **Fecha** | 16 de octubre de 2026 |
| **Autor** | [Nicolás Andrés Cano Leal](#autor) |

Biblioteca de consulta para un roadmap **DevOps → SRE → Arquitecto Fullstack (IA, Cloud, Software)**:
**826 comandos y 2.090 ejemplos** sobre 8 entornos. Cada comando trae descripción, sintaxis, ejemplos de
uso común, notas con trampas reales (Ubuntu vs AlmaLinux, PowerShell 5.1 vs 7, Helm 4, `use_lockfile` de
Terraform…), nivel, tags y la ruta del roadmap a la que pertenece. Incluye además mis **12 skills de
ingeniería** —los estándares con los que trabajo— como documentación navegable.

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

- **Frontend**: NiceGUI 3 (puerto 8090) con tres temas: **Dark**, **Luffy · Quinta Marcha** y
  **Eren · Titán Fundador**.
- **Backend**: FastAPI con SQLAlchemy 2 (`Mapped[]`), Pydantic v2 y psycopg v3.
- **Persistencia**: PostgreSQL 18 (comandos, favoritos, comandos propios y skills).
- **Todo dockerizado** con Compose.

Los JSON de `backend/app/seed/data/` son la **única fuente de verdad** del contenido: se validan contra un
contrato estricto y se vuelcan a la base de datos en cada arranque, sin pisar favoritos ni los comandos que
agregues desde la interfaz.

## Arquitectura

```
CmdVault/
├── .github/                  # CI (workflows/ci.yml), Dependabot, plantillas de issue/PR
├── docker-compose.yml        # db (postgres:18-alpine) + backend + frontend, encadenados por healthcheck
├── .env.example              # plantilla de variables (copiar a .env)
├── scripts/
│   ├── verificar.sh          # los mismos jobs que el CI, en el mismo orden
│   └── smoke.sh              # healthchecks + render de las 23 rutas contra el stack levantado
├── backend/
│   ├── Dockerfile            # multi-stage, no-root (UID 1000), HEALTHCHECK a /healthz
│   ├── requirements.txt · requirements-dev.txt
│   ├── app/
│   │   ├── config.py         # pydantic-settings, todo desde el entorno
│   │   ├── main.py           # create_app(), lifespan con init_db() bajo advisory lock, /healthz
│   │   ├── db.py · models.py # motor, sesiones y modelos ORM (Category, Command, Skill)
│   │   ├── repository.py     # TODO el SQL: búsqueda, CRUD, facetas, estadísticas
│   │   ├── search.py         # lógica pura: parser de consultas (tag:, level:, "frases")
│   │   ├── errors.py         # excepciones de dominio -> HTTP con un único handler
│   │   ├── api.py            # rutas finas: validan, llaman al repositorio, serializan
│   │   └── seed/
│   │       ├── schema.py     #   contrato pydantic del contenido (extra="forbid")
│   │       ├── loader.py     #   lectura y fusión de JSON + skills (puro, sin BD)
│   │       ├── sync.py       #   sincronización idempotente con la BD
│   │       ├── validate.py   #   validador para CI: contrato + títulos duplicados
│   │       ├── data/         #   37 JSON con los 826 comandos
│   │       └── skills/       #   12 SKILL.md de ingeniería
│   └── tests/                # pytest: lógica pura, seed, API (TestClient); SQLite o Postgres
└── frontend/
    ├── Dockerfile            # multi-stage, no-root (UID 1000), HEALTHCHECK a /healthz
    ├── requirements.txt · requirements-dev.txt
    ├── app/
    │   ├── config.py         # BACKEND_URL, API_KEY, STORAGE_SECRET, tema por defecto
    │   ├── api_client.py     # httpx: único acceso a datos; las lecturas nunca lanzan
    │   ├── themes.py         # paletas de los tres temas (datos puros)
    │   ├── langs.py          # lexer de Pygments según entorno y código (puro)
    │   ├── layout.py         # marco común: tema, cabecera con buscador, menú lateral
    │   ├── components.py     # tarjeta de comando, lista paginada
    │   ├── pages.py          # páginas @ui.page
    │   └── main.py           # ciclo de vida del cliente, /healthz, ui.run
    └── tests/                # pytest: temas, lenguajes, cliente HTTP con transporte simulado
```

Flujo: navegador → **frontend** (NiceGUI) → HTTP + `X-API-Key` → **backend** (FastAPI) → **db** (Postgres).
La UI nunca toca la base de datos, y la API key viaja solo de servidor a servidor: el navegador no la ve.

## Levantar con Docker

```bash
cp .env.example .env
# Reemplaza POSTGRES_PASSWORD, API_KEY y STORAGE_SECRET (Compose se niega a arrancar sin ellos):
python -c "import secrets; print(secrets.token_urlsafe(32))"
docker compose up -d --build --wait   # espera a que los 3 servicios estén healthy
./scripts/smoke.sh                    # opcional: comprueba las 23 rutas
```

| Servicio | URL |
|---|---|
| Interfaz | <http://localhost:8090> |
| API + documentación OpenAPI | <http://localhost:8000/docs> |

La interfaz usa el **8090** a propósito: el 8080 lo ocupa el controller Jenkins local. Se cambia con
`FRONTEND_PORT`.

El backend crea el esquema y sincroniza el contenido al arrancar. Los datos viven en el volumen nombrado
`pg_data`: `docker compose down` los conserva; **`docker compose down -v` los borra** (favoritos y comandos
propios incluidos). Respaldo:

```bash
docker compose exec db pg_dump -U cmdvault cmdvault > backup_cmdvault.sql
```

## Correr en local sin Docker

Requiere Python 3.13+ (probado con 3.14.3). Sin `DATABASE_URL`, el backend usa SQLite.

```powershell
python -m venv env
env\Scripts\python -m pip install -r backend\requirements-dev.txt -r frontend\requirements-dev.txt

# Backend
cd backend
$env:API_KEY="dev-key-0123456789abc"
..\env\Scripts\python -m uvicorn app.main:app --reload --port 8000

# En otra terminal, frontend
cd frontend
$env:API_KEY="dev-key-0123456789abc"; $env:STORAGE_SECRET="dev-secret-0123456789"; $env:PORT="8090"
..\env\Scripts\python -m app.main   # http://localhost:8090
```

## Endpoints

Prefijo `/api/v1`. Las rutas de escritura exigen la cabecera `X-API-Key`.

| Método | Ruta | Qué hace |
|---|---|---|
| `GET` | `/healthz` | `SELECT 1` contra la BD; 200 `ok` o 503 `degraded` (sin prefijo) |
| `GET` | `/categories` | Entornos con su total de comandos |
| `GET` | `/categories/{slug}` · `/categories/{slug}/facets` | Un entorno; sus secciones, temas y niveles con conteo |
| `GET` | `/commands?q=&category=&section=&topic=&level=&favorites=&limit=&offset=` | Búsqueda paginada |
| `GET` | `/commands/{id}` | Ficha completa de un comando |
| `POST` | `/commands` | Crea un comando propio (201; 409 si el título ya existe en el entorno) |
| `PATCH` · `DELETE` | `/commands/{id}` | Edita o borra un comando propio (409 si es del seed) |
| `PUT` | `/commands/{id}/favorite` | Marca o desmarca favorito |
| `GET` | `/skills` · `/skills/{slug}` | Skills de ingeniería: resumen y contenido Markdown |
| `GET` | `/stats` | Totales: comandos, ejemplos, favoritos, por nivel y por roadmap |
| `POST` | `/admin/reseed` | Vuelve a sincronizar el contenido sin reiniciar |

Los errores de dominio salen con el mismo contrato:

```json
{"error": "not_found", "detail": "Categoría 'nada' no existe"}
```

| Código | HTTP | Cuándo |
|---|---|---|
| `not_found` | 404 | Entorno, comando o skill inexistente |
| `conflict` | 409 | Título duplicado o intento de editar/borrar un comando del seed |
| `unauthorized` | 401 | Falta `X-API-Key` o no coincide |

## La interfaz

- **Inicio** con estadísticas (comandos, ejemplos, entornos, skills, favoritos), reparto por roadmap y
  tarjetas por entorno.
- **Vista de entorno** con filtro por sección, tema y nivel, y búsqueda dentro del entorno.
- **Buscador global** en la cabecera, con filtros combinables:
  `tag:redes level:avanzado` · `cat:kubernetes "rollout"` · `section:almalinux firewall`.
- **Tarjeta de comando**: botón para copiar, favorito y una sección desplegable con sintaxis, ejemplos
  resaltados según el lenguaje (bash, PowerShell, batch, Groovy, HCL, YAML, Dockerfile), notas, tags y roadmap.
- **Mis skills de ingeniería**, en Markdown.
- **Nuevo comando**: formulario con ejemplos dinámicos; los comandos propios se pueden borrar.
- **Selector de tema** guardado por usuario.

Si la API no responde, la interfaz muestra «Sin conexión con la API» y sigue funcionando.

## Variables de entorno

| Variable | Servicio | Por defecto | Para qué |
|---|---|---|---|
| `POSTGRES_PASSWORD` | db, backend | **obligatoria** | Contraseña de Postgres (Compose falla si falta) |
| `POSTGRES_USER` / `POSTGRES_DB` | db, backend | `cmdvault` | Usuario y base |
| `DATABASE_URL` | backend | `sqlite:///./cmdvault.db` (Compose arma la de Postgres) | URL de SQLAlchemy |
| `API_KEY` | backend, frontend | **obligatoria** (≥ 16 caracteres) | Protege las escrituras; la usa el frontend hacia la API |
| `SEED_ON_STARTUP` | backend | `true` | Sincroniza el contenido en cada arranque |
| `CORS_ORIGINS` | backend | `["http://localhost:8090"]` | Orígenes permitidos (JSON) |
| `BACKEND_URL` | frontend | `http://localhost:8000` (Compose: `http://backend:8000`) | URL base de la API |
| `STORAGE_SECRET` | frontend | **obligatoria** (≥ 16 caracteres) | Firma la sesión donde se guarda el tema |
| `DEFAULT_THEME` | frontend | `eren` | `dark`, `luffy` o `eren` |
| `PAGE_SIZE` | frontend | `30` | Comandos por página |
| `BACKEND_PORT` / `FRONTEND_PORT` | compose | `8000` / `8090` | Puertos publicados |

## Agregar contenido

1. Editar o crear `backend/app/seed/data/<entorno>-<tema>.json` según `app/seed/schema.py`
   (ejemplo válido en `app/seed/ejemplo.json.txt`).
2. Validar: `cd backend && python -m app.seed.validate` (rechaza campos extra y títulos duplicados).
3. `docker compose up -d --build backend`: el arranque sincroniza.

Las skills se copian desde `~/.claude/skills/*/SKILL.md` a `backend/app/seed/skills/`.

## Verificación

```bash
./scripts/verificar.sh              # todo
./scripts/verificar.sh --sin-docker # solo lint y tests
```

Reproduce los jobs de [`.github/workflows/ci.yml`](.github/workflows/ci.yml) en el mismo orden, con el
mismo ejecutable `pytest` que el CI, y sale con código ≠ 0 si algo falla:

1. **lint**: `ruff check` y `ruff format --check` de backend y frontend, validación del contenido y
   hadolint de ambos Dockerfiles.
2. **test-backend**: 30 tests sobre SQLite en memoria, cobertura ≥ 90 % (actual 97 %).
3. **test-postgres**: la misma suite contra un Postgres 18 desechable.
4. **test-frontend**: 23 tests, cobertura ≥ 80 % (actual 89 %).
5. **build**: `docker compose up --build --wait` en un proyecto aparte (`cmdvault-verificar`, puertos
   18000/18090, secretos efímeros), `smoke.sh` (23 rutas, incluida la de cada entorno) y `down -v`, también
   si algo falla. No toca tu stack ni tus datos.

Los tests del backend usan SQLite en memoria salvo que el entorno traiga `TEST_DATABASE_URL` (así corre
el job `test-postgres`).

## Decisiones de diseño

- **Contenido como código.** La biblioteca vive en JSON versionados y no en la base de datos: se revisa en
  PRs, se valida en CI y se reconstruye desde cero con un `up`. La BD guarda lo que es tuyo (favoritos y
  comandos propios).
- **Sincronización idempotente.** Upsert por (entorno, slug del título): conserva favoritos, actualiza lo
  modificado, borra lo retirado de los JSON y **nunca toca** los comandos creados desde la interfaz.
  Por eso los comandos del seed devuelven 409 si se editan por API.
- **Un arranque, N workers.** Uvicorn corre con 2 workers y cada uno ejecuta el `lifespan`. Con la BD vacía
  competirían en `create_all` y en los INSERT; `init_db()` toma un `pg_advisory_xact_lock` y el segundo
  worker espera a que el primero termine para encontrar la base ya cargada.
- **Capas.** Todo el SQL está en `repository.py`; `api.py` solo orquesta. La lógica pura (`search.py`,
  `seed/loader.py`, `themes.py`, `langs.py`) se prueba sin red ni BD.
- **Un único manejador de errores.** Subclases de `DomainError` con su código HTTP; ninguna ruta lanza
  `HTTPException` suelto.
- **Lecturas que nunca lanzan.** El cliente HTTP del frontend devuelve vacío y deja un log si la API cae;
  las escrituras devuelven `(ok, detalle)` para mostrar el motivo.
- **Tildes buscables.** El serializador JSON de SQLAlchemy usa `ensure_ascii=False`; con el valor por
  defecto, "métricas" se guardaba como `métricas` y el `LIKE` no lo encontraba.
- **Ejemplos con carga diferida.** `ui.code` de NiceGUI crea un temporizador por bloque, así que los
  ejemplos se construyen al abrir la tarjeta y no al listar.
- **Contenedores endurecidos.** Usuario no-root con UID numérico (listo para `runAsNonRoot`), sin `apt-get`
  (healthcheck en Python), backend con sistema de archivos de solo lectura y `tmpfs` en `/tmp`, y
  `no-new-privileges` en ambos servicios.

## Autor

**Nicolás Andrés Cano Leal**\
Backend Engineer → SRE | Python · Django · Kubernetes · Terraform · CI/CD

- LinkedIn: [linkedin.com/in/nicolasandrescl](https://www.linkedin.com/in/nicolasandrescl/)
- Portafolio: [nicolasandrescl.github.io](https://nicolasandrescl.github.io/)
- Correo: [nicolas.cano.leal@gmail.com](mailto:nicolas.cano.leal@gmail.com)

CmdVault v1.0.0 · 16 de octubre de 2026

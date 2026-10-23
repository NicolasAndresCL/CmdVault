# CmdVault — biblioteca personal para dominar la terminal: DevOps · SRE · Fullstack

[![CI](https://github.com/NicolasAndresCL/CmdVault/actions/workflows/ci.yml/badge.svg)](https://github.com/NicolasAndresCL/CmdVault/actions/workflows/ci.yml)
![Versión](https://img.shields.io/badge/versi%C3%B3n-1.2.0-blue)
![Python](https://img.shields.io/badge/python-3.14-3776AB)

| | |
|---|---|
| **Versión** | 1.2.0 |
| **Fecha** | 22 de octubre de 2026 |
| **Autor** | [Nicolás Andrés Cano Leal](#autor) |

Biblioteca de consulta para un roadmap **DevOps → SRE → Arquitecto Fullstack (IA, Cloud, Software)**:
**1.547 comandos y 4.184 ejemplos** sobre **18 entornos**, pensados para usar la terminal en todo, en
desarrollo y en producción (sitios web, servidores y VPS). Cada comando trae descripción, sintaxis, ejemplos
de uso común, notas con trampas reales (Ubuntu vs AlmaLinux, PowerShell 5.1 vs 7, Helm 4, `use_lockfile` de
Terraform, el volumen de Postgres 18…), nivel, tags y la ruta del roadmap a la que pertenece. Incluye además
mis **12 skills de ingeniería** —los estándares con los que trabajo— como documentación navegable.

El propio repositorio aplica lo que documenta: se **aprovisiona con Terraform**, se **configura y despliega
con Ansible** y se **verifica con Jenkins** y GitHub Actions.

| Entorno | Secciones | Comandos |
|---|---|---|
| Linux | Común · Ubuntu · AlmaLinux | 146 |
| Python | Python · Django · DRF · FastAPI | 115 |
| Windows | CMD · PowerShell · Windows Server | 145 |
| Jenkins | Pipeline · CLI · Docker · Administración | 66 |
| Docker | Imágenes · Contenedores · Compose · Redes y volúmenes · Build y registro · Sistema y diagnóstico | 122 |
| Kubernetes | kubectl básico · Workloads · Redes y servicios · Configuración y secretos · Troubleshooting · Helm · Clúster y contexto | 116 |
| Terraform | Flujo básico · Estado · Módulos y workspaces · HCL · Calidad y CI | 79 |
| Ansible | Ad-hoc · Playbooks · Inventario · Roles y Galaxy · Vault y secretos · Calidad y depuración | 78 |
| MySQL | Cliente y conexión · Consultas y esquema · Usuarios y permisos · Backup y restauración · Administración y rendimiento · Docker y producción | 71 |
| PostgreSQL | psql y conexión · Consultas y esquema · Roles y permisos · Backup y restauración · Rendimiento y diagnóstico · Administración y producción | 76 |
| MongoDB | mongosh y conexión · CRUD y consultas · Índices y agregación · Usuarios y seguridad · Backup y herramientas · Administración y producción | 56 |
| AWS | Configuración e identidad · Cómputo (EC2) · Almacenamiento (S3) · Redes y DNS · Bases de datos y contenedores · Serverless y mensajería · Monitoreo y costos | 90 |
| Cloud | Google Cloud (gcloud) · Azure (az) · DigitalOcean (doctl) · Cloudflare (wrangler) · Hetzner (hcloud) | 73 |
| Servidores web | Nginx · Apache · Caddy · TLS y certificados · Pruebas HTTP y diagnóstico | 75 |
| VPS y producción | Primer acceso y hardening · Usuarios y SSH · Despliegue · Servicios y procesos · Backups · Monitoreo y logs · Mantenimiento | 76 |
| Claude | Claude Code (sesiones, automatización, permisos, MCP/plugins/agentes, dentro de la sesión) · API con curl · CLI ant · SDK Python | 63 |
| Git y GitHub | Configuración · Día a día · Ramas y merge · Rebase e historial · Remotos · Deshacer y recuperar · Inspección y búsqueda · Avanzado · GitHub CLI (gh) | 59 |
| Terminal | Atajos y shell · Búsqueda moderna · JSON y YAML · tmux · Vim y nano · Scripting robusto · Productividad | 41 |
| **Total** | | **1.547** |

- **Frontend**: NiceGUI 3 (puerto 8090) con tres temas: **Dark**, **Luffy · Quinta Marcha** y
  **Eren · Titán Fundador**.
- **Backend**: FastAPI con SQLAlchemy 2 (`Mapped[]`), Pydantic v2 y psycopg v3.
- **Persistencia**: PostgreSQL 18 (comandos, favoritos, comandos propios y skills).
- **Todo dockerizado** con Compose.
- **Infraestructura como código**: Terraform (VPS en AWS con estado remoto en S3), Ansible (Ubuntu y
  AlmaLinux) y un `Jenkinsfile` para el Jenkins local.

Los JSON de `backend/app/seed/data/` son la **única fuente de verdad** del contenido: se validan contra un
contrato estricto y se vuelcan a la base de datos en cada arranque, sin pisar favoritos ni los comandos que
agregues desde la interfaz.

## Arquitectura

```
CmdVault/
├── .github/                  # CI (workflows/ci.yml), release por tag (release.yml), Dependabot, plantillas
├── Jenkinsfile               # mismo pipeline para el Jenkins local + deploy con Ansible (con aprobación)
├── docker-compose.yml        # db (postgres:18-alpine) + backend + frontend, encadenados por healthcheck
├── compose.traefik.yml       # override: detrás de un Traefik existente (sin puertos, basic auth, mem_limit)
├── .env.example              # plantilla de variables (copiar a .env)
├── scripts/
│   ├── verificar.sh          # los mismos jobs que el CI, en el mismo orden
│   ├── lint-iac.sh           # Terraform fmt/validate, tflint, Trivy y ansible-lint en contenedores
│   └── smoke.sh              # healthchecks + render de 33 rutas (una por entorno) contra el stack
├── infra/
│   ├── terraform/
│   │   ├── modules/vps/      # EC2 Ubuntu 24.04 + IP elástica + security group (SSH solo admin), IMDSv2
│   │   └── envs/prod/        # backend S3 con use_lockfile, lockfile multiplataforma, *.example
│   └── ansible/
│       ├── playbooks/site.yml        # common -> docker -> cmdvault
│       ├── roles/common/     # paquetes, usuario deploy, sshd endurecido, ufw/firewalld, fail2ban
│       ├── roles/docker/     # Docker Engine del repo oficial (deb822 / docker-ce.repo)
│       ├── roles/cmdvault/   # git clone, .env desde Vault, compose up --wait, chequeo de /healthz
│       └── group_vars/cmdvault/      # vars.yml + vault.yml.example (secretos con ansible-vault)
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
│   │       ├── data/         #   70 JSON con los 1.547 comandos
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
./scripts/smoke.sh                    # opcional: comprueba 33 rutas, una por entorno
docker compose down                   # al terminar de probar: bájalo (los datos se conservan)
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

## Desplegar en un VPS (Terraform + Ansible + Jenkins)

Tres capas, cada una con una sola responsabilidad: **Terraform** crea la máquina, **Ansible** la deja lista
y despliega, y **Jenkins** (o tú, desde la terminal) orquesta con aprobación humana.

**1. Infraestructura (AWS) — `infra/terraform/envs/prod`**

```bash
cd infra/terraform/envs/prod
cp backend.hcl.example backend.hcl                 # bucket S3 del estado (con versionado y cifrado)
cp terraform.tfvars.example terraform.tfvars       # tu llave pública y tu IP /32
terraform init -backend-config=backend.hcl
terraform plan -out=tfplan                         # revisar línea por línea antes de aplicar
terraform apply tfplan
terraform output -raw inventario_ansible           # bloque listo para el inventario de Ansible
```

Crea una EC2 Ubuntu 24.04 (`t3.small`, gp3 cifrado, IMDSv2 obligatorio) con IP elástica. El security group
solo deja entrar SSH desde los CIDR de `cidr_admin_ssh` (sin default, y `0.0.0.0/0` se rechaza en la
validación) y HTTP/HTTPS públicos. Si ya tienes un VPS (p. ej. AlmaLinux en HostGator), sáltate este paso.

**2. Configuración y despliegue — `infra/ansible`**

```bash
cd infra/ansible
cp inventory/hosts.yml.example inventory/hosts.yml
cp group_vars/cmdvault/vault.yml.example group_vars/cmdvault/vault.yml   # poner secretos reales
ansible-vault encrypt group_vars/cmdvault/vault.yml
ansible-galaxy collection install -r requirements.yml -p ./collections
ansible-playbook playbooks/site.yml --ask-vault-pass                        # todo
ansible-playbook playbooks/site.yml --tags deploy --ask-vault-pass -e cmdvault_version=v1.2.0  # solo redeploy
```

| Rol | Qué hace (Ubuntu y AlmaLinux) |
|---|---|
| `common` | Paquetes base, zona horaria, usuario `deploy` con llave SSH, `sshd` endurecido (validado con `sshd -t` antes de escribir), ufw o firewalld con 22/80/443, fail2ban y actualizaciones automáticas |
| `docker` | Docker Engine y el plugin Compose desde el repositorio oficial (deb822 en Ubuntu, `docker-ce.repo` en AlmaLinux) |
| `cmdvault` | `git clone` de la versión pedida, `.env` generado desde Vault (`0600`, `no_log`), `docker compose up --wait` y comprobación de `/healthz` de la API y la UI |

En producción la UI queda en el puerto 80 y la API solo en `127.0.0.1:8000`.

**3. Pipeline — `Jenkinsfile`**

Para el Jenkins local tal como está (sin el plugin Docker Pipeline): cada paso corre en un contenedor
efímero con `docker run --rm --volumes-from` y reproduce el CI de GitHub. Con `DEPLOY=true` en `main`, pide
aprobación (`input`) y ejecuta el playbook con las credenciales del credential store (`cmdvault-vps-ssh`,
`cmdvault-vault-pass`, `cmdvault-inventory`, `cmdvault-vault-vars`, `cmdvault-known-hosts`).

En el controller, el job **multibranch `cmdvault`** lo crea un script idempotente de `init.groovy.d`
(`80-cmdvault-job.groovy`, fuera de este repo): fuente git del repo público, sin credencial, y escaneo cada
hora mientras Jenkins esté encendido (GitHub no puede llamar a un Jenkins en `localhost`, así que no hay webhook).

### Servidor que ya tiene Traefik (p. ej. junto a n8n)

Si los puertos 80/443 ya son de un Traefik con Let's Encrypt, no se usa el rol `cmdvault` (publica la UI en
el 80): se aplica `compose.traefik.yml` encima del compose base.

| Qué hace el override | Por qué |
|---|---|
| Quita **todos** los puertos publicados (`ports: !reset []`) | Los puertos que publica Docker se saltan firewalld/ufw; la API queda solo en la red interna |
| Conecta solo el frontend a la red de Traefik, con sus etiquetas | Router HTTPS por `CMDVAULT_HOST`, certificado del resolver existente |
| Basic auth en Traefik | CmdVault no tiene usuarios y la UI permite escribir (comandos propios, favoritos) |
| `mem_limit`: db 256 MiB · backend 384 MiB · frontend 384 MiB | Servidor compartido. En reposo, medido: 53 · 218 · 93 MiB (~365 MiB en total) |

```bash
sudo git clone https://github.com/NicolasAndresCL/CmdVault.git /opt/cmdvault && cd /opt/cmdvault
sudo git checkout v1.2.0
docker network ls                                  # red donde vive Traefik → TRAEFIK_NETWORK
openssl passwd -apr1                               # hash para CMDVAULT_BASIC_AUTH
sudo cp .env.example .env && sudo chmod 600 .env   # secretos + las variables del override (ver tabla)
# en el .env, para que un `docker compose` a secas siempre incluya el override (y nunca publique puertos):
#   COMPOSE_PATH_SEPARATOR=:
#   COMPOSE_FILE=docker-compose.yml:compose.traefik.yml
sudo docker compose up -d --build --wait
curl -sS -o /dev/null -w '%{http_code}\n' https://$CMDVAULT_HOST/          # 401 sin credenciales
```

Actualizar: `sudo git fetch --tags && sudo git checkout <tag>` y el mismo `sudo docker compose up -d --build --wait`. El
override lo valida el job de lint del CI (`docker compose config`) para que no se rompa en silencio.

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
  resaltados según el lenguaje (bash, PowerShell, batch, SQL, JavaScript de mongosh, Nginx, Apache, Groovy,
  HCL, YAML, Dockerfile, Python), notas, tags y roadmap.
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
| `BACKEND_PORT` / `FRONTEND_PORT` | compose | `8000` / `8090` | Puertos publicados (el override de Traefik los quita) |
| `CMDVAULT_HOST` | override Traefik | **obligatoria** | Nombre público, p. ej. `cmdvault.<ip-con-guiones>.sslip.io` |
| `TRAEFIK_NETWORK` | override Traefik | **obligatoria** | Red de Docker donde vive Traefik |
| `CMDVAULT_BASIC_AUTH` | override Traefik | **obligatoria** | `usuario:hash` (`openssl passwd -apr1`), **entre comillas simples** en el `.env` para que Compose no interprete los `$` |
| `TRAEFIK_CERTRESOLVER` / `TRAEFIK_ENTRYPOINT` | override Traefik | `le` / `websecure` | Resolver ACME y entrypoint HTTPS del Traefik existente |

## Agregar contenido

1. Editar o crear `backend/app/seed/data/<entorno>-<tema>.json` según `app/seed/schema.py`
   (ejemplo válido en `app/seed/ejemplo.json.txt`).
2. Validar: `cd backend && python -m app.seed.validate` (rechaza campos extra y títulos duplicados).
3. `docker compose up -d --build backend`: el arranque sincroniza.

Los comandos que aparecen trabajando en otros proyectos se anotan primero en una **bandeja** fuera del repo
(`~/.claude/cmdvault/bandeja.md`, skill `cmdvault-registro`) con los mismos campos de `CommandIn`, y se
importan por lotes a estos JSON. Al importar: IP, puertos y nombres reales se generalizan (`203.0.113.10`,
`2222`, `<usuario>`) porque el repo es público, y los títulos existentes no se renombran (perderían el favorito).

Las skills se copian desde `~/.claude/skills/*/SKILL.md` a `backend/app/seed/skills/`.

## Verificación

```bash
./scripts/verificar.sh              # todo
./scripts/verificar.sh --sin-docker # solo lint y tests
```

Reproduce los jobs de [`.github/workflows/ci.yml`](.github/workflows/ci.yml) en el mismo orden, con el
mismo ejecutable `pytest` que el CI, y sale con código ≠ 0 si algo falla:

1. **lint**: `ruff check` y `ruff format --check` de backend y frontend, validación del contenido,
   hadolint de ambos Dockerfiles y que ningún `.sh` esté en git sin bit de ejecución.
2. **iac** (`scripts/lint-iac.sh`): `terraform fmt -check` y `validate`, tflint (ruleset AWS), Trivy
   (HIGH/CRITICAL) y `ansible-playbook --syntax-check` + `ansible-lint` con el perfil **production**.
3. **test-backend**: 30 tests sobre SQLite en memoria, cobertura ≥ 90 % (actual 97 %).
4. **test-postgres**: la misma suite contra un Postgres 18 desechable.
5. **test-frontend**: 35 tests, cobertura ≥ 80 % (actual 90 %).
6. **build**: `docker compose up --build --wait` en un proyecto aparte (`cmdvault-verificar`, puertos
   18000/18090, secretos efímeros), `smoke.sh` (33 rutas, una por cada entorno que la API declara) y
   `down -v`, también si algo falla. No toca tu stack ni tus datos.

El `Jenkinsfile` corre los mismos pasos (lint, IaC, tests en paralelo con Postgres como sidecar, build y
smoke en un proyecto `cmdvault-ci-<build>` que siempre se baja en `post`).

Al pushear un tag `vX.Y.Z`, [`release.yml`](.github/workflows/release.yml) comprueba que coincide con la
versión de `backend/pyproject.toml` y publica la GitHub Release con la sección de esa versión del CHANGELOG.

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
- **Un script de IaC para tres pipelines.** GitHub Actions, Jenkins y `verificar.sh` llaman al mismo
  `lint-iac.sh`, con versiones de Terraform, tflint, Trivy y Ansible fijadas en un solo lugar. Todo en
  contenedores `--rm`: nada que instalar en Windows (donde Ansible no corre como nodo de control).
- **Jenkins sin plugins nuevos.** El controller no tiene Docker Pipeline y su `JENKINS_HOME` es un volumen
  nombrado, así que `docker run -v $WORKSPACE` apuntaría a una ruta inexistente en el host. `--volumes-from`
  hereda los volúmenes del controller y el contenedor del paso ve el mismo workspace.
- **Terraform crea, Ansible configura.** Sin `user_data`: la máquina nace vacía y el mismo playbook sirve
  para la EC2 y para un VPS existente. Estado en S3 con `use_lockfile` (DynamoDB está deprecado), lockfile
  con hashes para Linux, Windows y macOS, SSH nunca abierto a `0.0.0.0/0` y salida solo por 80/443 (la
  excepción de Trivy está justificada en el código).
- **Secretos solo donde corresponde.** `.env` del servidor generado por Ansible desde Vault con `no_log`;
  en Jenkins todo pasa por el credential store, y el deploy verifica la host key contra un `known_hosts`
  conocido, nunca con `StrictHostKeyChecking=no`.
- **Lo que se levanta para probar, se baja.** Todo stack de prueba (verificación local, Jenkins, CI) usa
  proyecto y puertos propios y se baja con `down -v` en un `trap` o en `post { always }`.

## Autor

**Nicolás Andrés Cano Leal**\
Backend Engineer → SRE | Python · Django · Kubernetes · Terraform · CI/CD

- LinkedIn: [linkedin.com/in/nicolasandrescl](https://www.linkedin.com/in/nicolasandrescl/)
- Portafolio: [nicolasandrescl.github.io](https://nicolasandrescl.github.io/)
- Correo: [nicolas.cano.leal@gmail.com](mailto:nicolas.cano.leal@gmail.com)

CmdVault v1.2.0 · 22 de octubre de 2026

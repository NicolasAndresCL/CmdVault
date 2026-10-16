---
name: docker
description: >
  Estándares de contenerización de Nicolás Cano Leal: imágenes multi-stage,
  no-root, healthchecks y Compose para desarrollo local. USAR SIEMPRE que se
  cree o revise un Dockerfile, docker-compose.yml, .dockerignore, o se discuta
  cómo empaquetar/desplegar un servicio en contenedor, o se elija entre
  volumen nombrado y bind mount (rendimiento en Docker Desktop, respaldo de
  volúmenes) — aunque no se pida explícitamente "sigue mis estándares". Aplica
  a backends Python/Django, workers, y cualquier servicio que vaya a producción
  o CI.
---

# Docker — estándares de Nicolás Cano Leal

> Referencia real y probada: `backend/Dockerfile`, `backend/docker-compose.yml` y
> `backend/.dockerignore` de TienditaMarian. Copiar el patrón, no reinventarlo.

## Reglas no negociables

1. **Multi-stage siempre.** Un stage `builder` compila (con `build-essential`,
   headers de dev) y un stage `runtime` solo copia el resultado. La imagen final
   no debe arrastrar compiladores ni cabeceras de desarrollo — menos peso, menos
   superficie de ataque.
2. **No-root.** Crear un usuario dedicado (`useradd --create-home --shell /bin/bash
   <app>`) y `USER <app>` antes del `CMD`. Un proceso comprometido dentro del
   contenedor no debe tener privilegios de root.
3. **Healthcheck obligatorio**, apuntando a un endpoint real de salud
   (`/healthz/`), no solo "el proceso sigue vivo":
   ```dockerfile
   HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
       CMD curl -fsS http://localhost:8000/healthz/ || exit 1
   ```
   **Diseñarlo según lo que significa "sano" para ESE sistema**, no copiar la
   receta. En un laboratorio hecho para romper cosas, un servicio caído a
   propósito no es una avería del contenedor (se acepta `degraded`), pero un bus
   de systemd que no responde sí. En un servicio web, un 200 que no toca la base
   de datos no prueba gran cosa.
4. **`.dockerignore` completo desde el día 1**: `.env`/`.env.*` (nunca meter
   secretos en una capa de la imagen), `env/`/`venv/`, `__pycache__/`, `.git/`,
   `.github/`, caches de test/lint (`.pytest_cache/`, `.ruff_cache/`,
   `htmlcov/`), `*.sqlite3`, `staticfiles/`, `media/`. Reduce el contexto de
   build y evita fugas.
5. **Imágenes `-slim`** (`python:3.12-slim`) como base, nunca `latest` a secas
   ni la imagen completa si no hace falta.
6. **Variables de entorno de runtime explícitas**: `PYTHONDONTWRITEBYTECODE=1`,
   `PYTHONUNBUFFERED=1` (logs sin buffer, se ven en tiempo real), `PIP_NO_CACHE_DIR=1`
   en el builder.

## Lo que se levanta para probar, se baja al terminar

**Norma fija de Nicolás (2026-10-16):** todo `docker compose up -d` (o `docker run -d`) que se haga
para **probar** algo termina con su `docker compose down` (o `docker stop`/`rm`) **en la misma tarea**,
antes del reporte final. Un stack de prueba olvidado ocupa puertos (choca con Jenkins en 8080, con el
siguiente proyecto), consume RAM de la VM de Docker Desktop y deja dudas de qué está corriendo.
(Origen: CmdVault, 2026-10-16 — el stack de prueba quedó arriba tras cerrar la tarea.)

- **Al cerrar la prueba**: `docker compose down` y comprobar con
  `docker ps -a --filter name=<proyecto>` que no quedó nada. Usar `down -v` solo si los volúmenes
  también son de prueba (nunca sobre datos reales sin confirmar).
- **En scripts de verificación**: proyecto aparte y puertos propios (`COMPOSE_PROJECT_NAME=<app>-verificar`,
  puertos 18xxx) para no tocar el stack de uso diario, y `trap '... compose down -v --remove-orphans' EXIT`
  para que se baje **aunque la prueba falle**. Contenedores sueltos con `--rm` + `trap 'docker stop ...'`.
- **Excepción**: solo queda arriba lo que Nicolás pidió explícitamente dejar corriendo (p. ej. "déjalo
  levantado para probarlo yo"); en ese caso decirlo en el reporte final con el comando para bajarlo.
- En el reporte final, **decir qué se bajó** (y qué volúmenes se conservaron).

## Esqueleto de referencia (Django + gunicorn)

```dockerfile
# ---------------------------------------------------------------- build
FROM python:3.12-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*
COPY requirements/ requirements/
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install -r requirements/prod.txt

# ---------------------------------------------------------------- runtime
FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/opt/venv/bin:$PATH"
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 curl \
    && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home --shell /bin/bash app
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --chown=app:app . .
RUN mkdir -p /app/staticfiles /app/media && chown -R app:app /app/staticfiles /app/media
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://localhost:8000/healthz/ || exit 1
CMD ["sh", "-c", "python manage.py migrate --no-input && \
     python manage.py collectstatic --no-input && \
     gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 60"]
```

Notas: `libpq5` (runtime) en vez de `libpq-dev` (headers de compilación) en el
stage final — solo lo que hace falta para *correr*, no para *compilar*. `curl`
solo está para el healthcheck.

## Compose para desarrollo local

- Cada servicio con dependencia real (DB) usa `depends_on: condition:
  service_healthy`, no solo `depends_on` a secas — si el backend arranca antes
  de que Postgres acepte conexiones, el `migrate` del arranque falla con
  conexión rechazada.
- `healthcheck` en `db` con `pg_isready`.
- Secretos sin default inseguro silencioso: `SECRET_KEY: ${SECRET_KEY:?define
  SECRET_KEY en tu .env}` — falla ruidoso si falta, en vez de arrancar con una
  clave débil.
- Documentar en un comentario arriba del `docker-compose.yml` **para qué sirve
  levantar esto** (qué prueba solo corre así, ej. tests de concurrencia que
  SQLite no puede validar porque ignora `select_for_update`).
- Volúmenes nombrados para datos persistentes (`postgres_data`, `media_data`),
  nunca bind-mount del filesystem del host para la BD ni para ningún árbol
  con miles de ficheros que el proceso recorra al arrancar (plugins, `war`,
  `node_modules`, `.m2`). Ver *Almacenamiento: volumen vs bind mount* abajo.

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-app}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-app}"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build: .
    depends_on:
      db:
        condition: service_healthy
    environment:
      SECRET_KEY: ${SECRET_KEY:?define SECRET_KEY en tu .env}
    ports:
      - "8000:8000"

volumes:
  postgres_data:
```

## Almacenamiento: volumen vs bind mount

> Caso real y medido (Jenkins local, 18-09-2026): `JENKINS_HOME` con 4.599
> ficheros como bind mount de `C:\Users\...` → **7–11 min** de arranque. El
> mismo árbol en un volumen nombrado → **5–7 s**. Copiarlo a través del bind
> mount midió ≈6 MB/s.

1. **Camino caliente → volumen nombrado, siempre.** En Docker Desktop
   (Windows/macOS) el contenedor corre en una VM y cada acceso a un bind mount
   del host cruza la capa de traducción VM ↔ NTFS/APFS, pagando el peaje **por
   operación de fichero**. Una BD con pocos ficheros grandes lo disimula; un
   árbol de miles de ficheros pequeños lo convierte en minutos. En Linux nativo
   (o desde el ext4 de WSL2 hacia un motor en la misma VM) bind mount y volumen
   empatan: la trampa es específica de rutas `C:\...` / `/mnt/c/...`.
2. **Bind mount solo para lo que el host necesita tocar**: configuración
   editable, fuentes de secretos, un buzón de ficheros de entrada. Pocas
   decenas de ficheros. Es el caso de uso que la propia documentación de Docker
   le asigna (*"if you need to access files from both containers and the
   host"*), frente a los volúmenes (*"when your application requires
   high-performance I/O"*).
3. **Los dos conviven.** Un bind mount de una subcarpeta montado **encima** de
   un volumen funciona: Docker ordena los montajes por longitud de la ruta
   destino, así que el padre va primero y dentro del contenedor hay un único
   árbol.
   ```yaml
   volumes:
     - app_home:/var/app                       # volumen: el grueso, I/O nativo
     - ./config:/var/app/config                # bind: lo que se edita desde fuera
     - ./entrada:/var/app/entrada              # bind: buzón de ficheros
   ```
4. **Un volumen cambia el modelo de persistencia, no solo la velocidad.**
   Sobrevive a `docker rm`, a `compose down` y a reiniciar Docker Desktop;
   **no** sobrevive a `docker volume rm`, a `compose down -v` ni a *Clean /
   Purge data* / *Reset to factory defaults* de Docker Desktop — cosas que una
   carpeta del host sí aguanta. El mismo día que se migra a volumen:
   - declararlo `external: true` (creado a mano; Compose no lo borra), y
   - dejar un respaldo que lo exporte desde un contenedor auxiliar — la lectura
     ocurre dentro de la VM, así que es rápida; solo el `.tgz` cruza al host:
     ```powershell
     docker run --rm -v app_home:/datos:ro -v C:\dev\backups:/respaldo alpine `
         sh -c "tar -czf /respaldo/app_home_$(Get-Date -f yyyy-MM-dd).tgz -C /datos ."
     ```
5. **Migrar con verificación**: `cp -a /origen/. /destino/` desde `alpine` con
   ambos montados, y comparar `find -type f | wc -l` a ambos lados antes de
   tocar el compose. Dejar el volumen con dueño del usuario de la imagen
   (`chown -R 1000:1000`) aunque hoy se corra como root: prepara el retiro de
   `user: root`. Los bind mounts de Windows son `root` `0777` y **no es
   configurable** (documentado por Docker): si algo falla al pasar a no-root,
   serán ellos, no el volumen.
6. **Remedir lo que dependía del montaje**: el `start_period` del healthcheck,
   los timeouts de espera en scripts y CI, los tiempos documentados. Un
   `start_period: 15m` heredado del bind mount tarda un cuarto de hora en
   avisar de un contenedor realmente roto.

## Trampas conocidas

- **La imagen oficial de MySQL corrompe acentos/ñ de cualquier `.sql` UTF-8 del
  init, en todas sus versiones** (medido 2026-09-19 con `mysql:9.7` y `8.4`:
  `ñ` → `C383C2B1`). No es el charset del servidor (`utf8mb4`) sino el del
  **cliente** `mysql` que usa el entrypoint: lo elige por el *locale* y el
  contenedor arranca en `POSIX` → `latin1`. Cambiar de tag no sirve. Arreglo:
  `LANG: C.UTF-8` en el `environment:` del servicio (cubre el init y todo
  `docker exec … mysql`); `SET NAMES utf8mb4;` en el script solo cubre el init.
  La imagen de MariaDB ya exporta `LANG=C.UTF-8`, por eso "no tiene el bug".
  Antes de sustituir una imagen "por una limpia", levantar cada candidata en un
  contenedor desechable con el mismo script y comparar `HEX()`: dos minutos que
  evitan recrear un volumen para volver a ver lo mismo.
- **En Compose, el entorno del shell manda sobre `--env-file`.** Una variable
  exportada por un script anterior en la misma consola (p. ej. una `SECRET_KEY`
  efímera para `check --deploy`) gana a la del archivo, y `up` arranca el
  servicio con un valor que no está en ningún sitio, sin aviso (All in Django,
  2026-09-02: 14 días así). Todo script que exporte variables las limpia al
  salir (`Remove-Item Env:X`); antes de un `up`, comprobar que el shell no las
  tiene. Y para detectar drift **no** comparar `docker compose config --hash`
  con la label `com.docker.compose.config-hash`: en servicios con `env_file`
  difieren aunque el contenedor acabe de crearse. La prueba real es un segundo
  `up -d`: `Running` sin recrear = sin drift. Comparar `Config.Env` del
  contenedor con `docker compose config` variable a variable sí funciona.
- **Un volumen anónimo que ningún `docker ps -a` monta puede no ser huérfano.**
  Los contenedores de sistema de Docker Desktop (su Kubernetes: `etcd-desktop-
  control-plane`, `kubelet`, 1,2 GB de `/var`) están ocultos pero enlazan sus
  volúmenes: `docker system df -v` muestra `LINKS=1` y `docker volume ls -f
  dangling=true` no los lista. Borrarlos destruye el clúster. La vara para
  "huérfano" es el filtro `dangling=true` del daemon, y aun así mirar el
  contenido con `alpine` antes de un `rm`.
- **Tras `port is already allocated`, `docker start` deja el contenedor sin
  puertos.** El fallo ocurre al programar la red; el contenedor queda creado
  con los `PortBindings` en su config pero sin aplicarlos, y un `start` (o un
  segundo `up -d`, que solo arranca) no los reprograma: dentro responde 200,
  desde el host *connection refused* y `docker port <c>` sale vacío. Liberar el
  puerto y `docker compose up -d --force-recreate`; comprobar con `docker port`.
- **`docker exec` desde Git Bash reescribe rutas absolutas de Linux** a
  `C:/Program Files/Git/...` (conversión de rutas de MSYS). Anteponer
  `MSYS_NO_PATHCONV=1` o envolver en `sh -c '...'`. El `//var/run/docker.sock`
  con doble barra es la misma trampa vista desde el compose.
- **`SHELL` y `ARG` NO se heredan entre etapas.** Tras cada `FROM ... AS <etapa>`
  hay que redeclarar los `ARG` que se usen y, si algún `RUN` lleva un pipe,
  también `SHELL ["/bin/bash", "-o", "pipefail", "-c"]`. Sin él se vuelve al `sh`
  por defecto, donde un fallo a la izquierda del pipe pasa desapercibido y la capa
  se da por buena (hadolint lo canta como DL4006).
- **Al dividir un Dockerfile en etapas, volver a pasar hadolint.** Haberlo pasado
  antes de la división no vale: la refactorización es justo lo que introduce los
  fallos de herencia entre etapas.
- **`--build-arg` no es un mecanismo de secretos**: el valor queda registrado en
  `docker history` de la imagen resultante. Para secretos de verdad, `--secret` de
  BuildKit; para una contraseña de desarrollo, documentar la limitación.

- Sin `SECURE_HTTPS`/toggle equivalente, correr detrás de un proxy local sin
  TLS con `SECURE_SSL_REDIRECT=True` produce un **bucle infinito de
  redirecciones**. Exponer la variable como env var togglable en Compose.
- Copiar `requirements/` *antes* que el resto del código en el Dockerfile:
  aprovecha la cache de capas de Docker (si el código cambia pero las
  dependencias no, no se reinstala nada).
- No usar `COPY . .` en el builder si ya se copió selectivamente — duplica
  contexto y rompe cache.

## Ver también
[[github-actions]] para construir y publicar la imagen en CI · [[python-backend]]
para lo que corre dentro del contenedor · [[kubernetes]] para orquestar esta
imagen en un clúster (el `runAsNonRoot` del pod exige el usuario que se crea
aquí) · [[terraform]] para la infraestructura donde corre.

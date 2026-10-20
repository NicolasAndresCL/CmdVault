#!/usr/bin/env bash
# Reproduce en local TODOS los jobs de .github/workflows/ci.yml, en el mismo orden.
# Uso (Git Bash, desde la raíz): ./scripts/verificar.sh [--sin-docker]
set -euo pipefail
cd "$(dirname "$0")/.."
PY=env/Scripts/python.exe; [[ -x $PY ]] || PY=env/bin/python
PY="$(pwd)/$PY"
# Mismo entrypoint que el CI: `pytest`, no `python -m pytest` (este último añade el cwd
# al sys.path y oculta un `ModuleNotFoundError: app` que en el runner sí revienta).
PYTEST="$(dirname "$PY")/pytest"
export PYTHONIOENCODING=utf-8
paso() { printf '\n\033[1;34m== %s\033[0m\n' "$1"; }

paso "lint: ruff + formato + contrato del seed"
"$PY" -m ruff check backend frontend
"$PY" -m ruff format --check backend frontend
(cd backend && "$PY" -m app.seed.validate)
# En Windows (core.filemode=false) un .sh nuevo entra como 100644 y en el runner Linux da
# "Permission denied"; Git Bash lo ejecuta igual, así que solo se ve mirando el índice.
if git ls-files -s -- '*.sh' | grep -v '^100755'; then
  echo "Scripts sin bit de ejecución en git: git update-index --chmod=+x <archivo>"; exit 1
fi
# Override de producción detrás de Traefik: YAML válido y `!reset` soportado (no necesita daemon).
POSTGRES_PASSWORD=ci API_KEY=ci STORAGE_SECRET=ci CMDVAULT_HOST=cmdvault.ci.example \
  TRAEFIK_NETWORK=ci CMDVAULT_BASIC_AUTH=ci:x \
  docker compose -f docker-compose.yml -f compose.traefik.yml config --quiet

[[ "${1:-}" == "--sin-docker" ]] || { paso "iac: Terraform + Ansible"; ./scripts/lint-iac.sh; }

paso "test-backend (SQLite, cobertura >= 90)"
(cd backend && "$PYTEST" -rs --cov --cov-fail-under=90 -q)

paso "test-frontend (cobertura >= 80)"
(cd frontend && "$PYTEST" -rs --cov --cov-fail-under=80 -q)

[[ "${1:-}" == "--sin-docker" ]] && { echo "Saltando jobs con Docker"; exit 0; }

paso "test-postgres (Postgres 18 efímero en :5433)"
docker rm -f cmdvault-pgtest >/dev/null 2>&1 || true
docker run -d --rm --name cmdvault-pgtest -e POSTGRES_USER=app -e POSTGRES_PASSWORD=app \
  -e POSTGRES_DB=app_test -p 5433:5432 postgres:18-alpine >/dev/null
trap 'docker stop cmdvault-pgtest >/dev/null 2>&1 || true' EXIT
until docker exec cmdvault-pgtest pg_isready -U app -d app_test >/dev/null 2>&1; do sleep 1; done
sleep 1
(cd backend && TEST_DATABASE_URL=postgresql+psycopg://app:app@localhost:5433/app_test "$PYTEST" -rs -q)

paso "build: hadolint + compose up --wait + smoke (proyecto aparte, se baja al terminar)"
for f in backend frontend; do docker run --rm -i hadolint/hadolint < "$f/Dockerfile"; done
# Proyecto y puertos propios: no toca el stack de uso diario ni sus datos.
# Secretos efímeros solo para esta prueba; nunca se escriben a disco.
export COMPOSE_PROJECT_NAME=cmdvault-verificar BACKEND_PORT=18000 FRONTEND_PORT=18090
export POSTGRES_PASSWORD API_KEY STORAGE_SECRET
POSTGRES_PASSWORD=$("$PY" -c "import secrets; print(secrets.token_hex(16))")
API_KEY=$("$PY" -c "import secrets; print(secrets.token_hex(24))")
STORAGE_SECRET=$("$PY" -c "import secrets; print(secrets.token_hex(24))")
trap 'docker stop cmdvault-pgtest >/dev/null 2>&1 || true; docker compose down -v --remove-orphans >/dev/null 2>&1 || true' EXIT
docker compose up -d --build --wait --wait-timeout 180
./scripts/smoke.sh "http://localhost:$FRONTEND_PORT" "http://localhost:$BACKEND_PORT"
docker compose down -v --remove-orphans
printf '\n\033[1;32mTodo el pipeline en verde (stack de prueba bajado).\033[0m\n'

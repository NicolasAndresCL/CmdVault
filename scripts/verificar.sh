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

paso "build: hadolint + compose up --wait + smoke"
for f in backend frontend; do docker run --rm -i hadolint/hadolint < "$f/Dockerfile"; done
docker compose up -d --build --wait --wait-timeout 180
./scripts/smoke.sh
printf '\n\033[1;32mTodo el pipeline en verde.\033[0m\n'

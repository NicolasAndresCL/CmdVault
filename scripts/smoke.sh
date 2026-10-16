#!/usr/bin/env bash
# Smoke test del stack levantado: healthchecks + render de cada página de la UI.
# Uso: ./scripts/smoke.sh [UI_URL] [API_URL]
set -euo pipefail
UI="${1:-http://localhost:8090}"
API="${2:-http://localhost:8000}"
fallos=0

check() {  # check <url> <código esperado>
  local code
  code=$(curl -s -o /dev/null -w '%{http_code}' "$1")
  if [[ "$code" == "$2" ]]; then echo "  OK   $code $1"; else echo "  FAIL $code $1 (esperado $2)"; fallos=$((fallos+1)); fi
}

echo "API"
check "$API/healthz" 200
check "$API/api/v1/categories" 200
check "$API/api/v1/stats" 200
check "$API/api/v1/commands?q=tag:redes" 200
check "$API/api/v1/skills" 200
check "$API/api/v1/commands" 200
check "$API/api/v1/categories/no-existe" 404

echo "UI"
check "$UI/healthz" 200
for p in / /favoritos /skills /skills/docker /nuevo "/buscar?q=compose" /comando/1; do check "$UI$p" 200; done
# Una página por entorno, según lo que la API diga que existe (no una lista fija que se desactualiza).
for c in $(curl -s "$API/api/v1/categories" | python3 -c 'import json,sys; print(" ".join(c["slug"] for c in json.load(sys.stdin)))'); do
  check "$UI/c/$c" 200
done

total=$(curl -s "$API/api/v1/stats" | python3 -c 'import json,sys; print(json.load(sys.stdin)["commands"])')
echo "Comandos en la biblioteca: $total"
[[ "$total" -ge 1000 ]] || { echo "  FAIL: seed casi vacío"; fallos=$((fallos+1)); }

[[ $fallos -eq 0 ]] && echo "Smoke OK" || { echo "$fallos fallos"; exit 1; }

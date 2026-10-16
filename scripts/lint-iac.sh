#!/usr/bin/env bash
# Valida la infraestructura como código con herramientas en contenedores efímeros (--rm):
# Terraform (fmt, validate), tflint, Trivy (seguridad) y Ansible (syntax-check, ansible-lint).
# Lo usan por igual GitHub Actions, el Jenkinsfile y scripts/verificar.sh.
# Uso (desde la raíz): ./scripts/lint-iac.sh
set -euo pipefail
cd "$(dirname "$0")/.."
export MSYS_NO_PATHCONV=1   # Git Bash: no reescribir rutas /work de los contenedores

TF_IMG=hashicorp/terraform:1.16.6
TFLINT_IMG=ghcr.io/terraform-linters/tflint:v0.64.0
TRIVY_IMG=aquasec/trivy:0.76.0
PY_IMG=python:3.14-slim
ANSIBLE_PKGS="ansible-core==2.21.5 ansible-lint==26.10.1"

# En Windows Docker necesita la ruta C:/...; en Linux, la normal.
RAIZ=$(pwd -W 2>/dev/null || pwd)
TF_DIR="$RAIZ/infra/terraform"
paso() { printf '\n\033[1;34m-- %s\033[0m\n' "$1"; }

paso "terraform fmt -check"
docker run --rm -v "$TF_DIR:/work" -w /work "$TF_IMG" fmt -recursive -check -diff

paso "terraform validate (envs/prod, sin backend)"
docker run --rm -v "$TF_DIR:/work" -w /work "$TF_IMG" -chdir=envs/prod init -backend=false -input=false -lockfile=readonly >/dev/null
docker run --rm -v "$TF_DIR:/work" -w /work "$TF_IMG" -chdir=envs/prod validate

paso "tflint"
docker run --rm -v "$TF_DIR:/data" -w /data --entrypoint sh "$TFLINT_IMG" \
  -c 'tflint --init --config /data/.tflint.hcl >/dev/null && tflint --recursive --config /data/.tflint.hcl'

paso "trivy config (HIGH/CRITICAL)"
docker run --rm -v "$TF_DIR:/src:ro" "$TRIVY_IMG" config --quiet --exit-code 1 \
  --severity HIGH,CRITICAL --skip-dirs /src/envs/prod/.terraform /src

paso "ansible syntax-check + ansible-lint (perfil production)"
docker run --rm -v "$RAIZ/infra/ansible:/ansible:ro" "$PY_IMG" sh -c "
  set -e
  cp -r /ansible /tmp/a && cd /tmp/a
  apt-get update -qq >/dev/null 2>&1 && apt-get install -y -qq git >/dev/null 2>&1
  pip install -q --root-user-action=ignore $ANSIBLE_PKGS >/dev/null 2>&1
  ansible-galaxy collection install -r requirements.yml -p ./collections >/dev/null
  ansible-playbook -i localhost, playbooks/site.yml --syntax-check
  ansible-lint --offline --profile production playbooks/site.yml roles"

printf '\n\033[1;32mIaC limpia.\033[0m\n'

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

# Montajes: en local/GitHub Actions, bind mount del repo. Dentro de Jenkins (Docker-outside-of-Docker
# con JENKINS_HOME en volumen nombrado) el workspace no existe en el host: con
# DOCKER_VOLUMES_FROM=<id del contenedor jenkins> se heredan sus volúmenes y se usa la misma ruta.
if [[ -n "${DOCKER_VOLUMES_FROM:-}" ]]; then
  TF_W="$(pwd)/infra/terraform"; ANS_W="$(pwd)/infra/ansible"
  M_TF=(--volumes-from "$DOCKER_VOLUMES_FROM"); M_ANS=("${M_TF[@]}")
else
  RAIZ=$(pwd -W 2>/dev/null || pwd)   # Windows necesita C:/...
  TF_W=/work; ANS_W=/ansible
  M_TF=(-v "$RAIZ/infra/terraform:/work"); M_ANS=(-v "$RAIZ/infra/ansible:/ansible:ro")
fi
paso() { printf '\n\033[1;34m-- %s\033[0m\n' "$1"; }

paso "terraform fmt -check"
docker run --rm "${M_TF[@]}" -w "$TF_W" "$TF_IMG" fmt -recursive -check -diff

paso "terraform validate (envs/prod, sin backend)"
docker run --rm "${M_TF[@]}" -w "$TF_W" "$TF_IMG" -chdir=envs/prod init -backend=false -input=false -lockfile=readonly >/dev/null
docker run --rm "${M_TF[@]}" -w "$TF_W" "$TF_IMG" -chdir=envs/prod validate

paso "tflint"
docker run --rm "${M_TF[@]}" -w "$TF_W" --entrypoint sh "$TFLINT_IMG" \
  -c "tflint --init --config $TF_W/.tflint.hcl >/dev/null && tflint --recursive --config $TF_W/.tflint.hcl"

paso "trivy config (HIGH/CRITICAL)"
docker run --rm "${M_TF[@]}" "$TRIVY_IMG" config --quiet --exit-code 1 \
  --severity HIGH,CRITICAL --skip-dirs "$TF_W/envs/prod/.terraform" "$TF_W"

paso "ansible syntax-check + ansible-lint (perfil production)"
docker run --rm "${M_ANS[@]}" "$PY_IMG" sh -c "
  set -e
  cp -r $ANS_W /tmp/a && cd /tmp/a
  apt-get update -qq >/dev/null 2>&1 && apt-get install -y -qq git >/dev/null 2>&1
  pip install -q --root-user-action=ignore $ANSIBLE_PKGS >/dev/null 2>&1
  ansible-galaxy collection install -r requirements.yml -p ./collections >/dev/null
  ansible-playbook -i localhost, playbooks/site.yml --syntax-check
  ansible-lint --offline --profile production playbooks/site.yml roles"

printf '\n\033[1;32mIaC limpia.\033[0m\n'

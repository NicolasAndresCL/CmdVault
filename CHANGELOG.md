# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/); versionado semántico.

## [1.0.1] — 16 de octubre de 2026

### Agregado
- **10 entornos nuevos** (672 comandos): MySQL, PostgreSQL, MongoDB, AWS, Cloud (GCP, Azure, DigitalOcean,
  Cloudflare, Hetzner), Servidores web (Nginx, Apache, Caddy, TLS), VPS y producción, Claude (Claude Code,
  API con curl, CLI `ant`, SDK Python), Git y GitHub (incluye `gh`) y Terminal (tmux, Vim, rg/fd/fzf,
  jq/yq, scripting). Total: 1.498 comandos y 4.078 ejemplos en 18 entornos.
- **Infraestructura como código del propio proyecto**:
  - `infra/terraform`: módulo `vps` (EC2 Ubuntu 24.04, IP elástica, SSH restringido, IMDSv2, disco cifrado)
    y entorno `prod` con estado en S3 y `use_lockfile`.
  - `infra/ansible`: roles `common`, `docker` y `cmdvault` para Ubuntu y AlmaLinux; secretos con
    ansible-vault.
  - `Jenkinsfile` para el Jenkins local: mismo pipeline que GitHub Actions y deploy con aprobación.
- `scripts/lint-iac.sh`: Terraform fmt/validate, tflint, Trivy y ansible-lint (perfil production) en
  contenedores, compartido por GitHub Actions, Jenkins y `verificar.sh`.
- Job `iac` en el CI. Resaltado de SQL, JavaScript (mongosh), Nginx, Apache y Python según el entorno.
- Skill `readme` entre las skills servidas (12).

### Cambiado
- `smoke.sh` recorre los entornos que declara la API en vez de una lista fija (33 rutas).
- `verificar.sh` usa el mismo ejecutable `pytest` que el CI, un proyecto de Compose aparte y baja el stack
  de prueba con `trap`, también si falla.

### Corregido
- CI: `pythonpath` de pytest (el ejecutable `pytest` no añade el cwd al `sys.path`).
- CI: scripts `.sh` sin bit de ejecución en git (creados en Windows).

## [1.0.0] — 16 de octubre de 2026

- Primera versión: FastAPI + NiceGUI + PostgreSQL 18 en Docker Compose, 826 comandos en 8 entornos,
  11 skills, tres temas, CI en GitHub Actions.

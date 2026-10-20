# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/); versionado semántico.

## [1.1.0] — 19 de octubre de 2026

### Agregado
- **`compose.traefik.yml`**: override para desplegar en un servidor que ya tiene Traefik en 80/443 (el VPS con
  n8n). Quita todos los puertos publicados (`!reset`), conecta solo el frontend a la red de Traefik con router
  HTTPS y certificado del resolver existente, exige basic auth y fija `mem_limit` (256/384/384 MiB, medidos
  en reposo: 53/218/93 MiB). Probado en local con Traefik v3.6: 401 sin credenciales, 200 con ellas, HTTP→HTTPS,
  404 para otros hosts, websocket de NiceGUI por `wss://` y puertos 8000/8090 cerrados en el host.
- Validación del override (`docker compose config`) en el job de lint del CI, en `verificar.sh` y en el
  Jenkinsfile.
- Job multibranch `cmdvault` en el Jenkins local, creado por un `init.groovy.d` idempotente.

## [1.0.2] — 19 de octubre de 2026

### Agregado
- **Primera importación de la bandeja** (`~/.claude/cmdvault/bandeja.md`, origen: hardening del VPS
  AlmaLinux con n8n): 12 comandos nuevos — total 1.510 comandos y 4.121 ejemplos.
  - VPS (+5): `firewall-offline-cmd` con el servicio apagado, *dead-man switch* con `systemd-run`, prueba
    externa de que SSH rechaza contraseñas, usuario administrador con `wheel` y medición de capacidad.
  - Linux (+3): `nc -zv` para distinguir abierto/cerrado/filtrado, probar `/etc/fstab` sin reiniciar y
    `vm.swappiness` con `tuned` activo.
  - Git (+2): `git ls-remote` antes del primer push y `gh label create`.
  - Docker (+1): probar workflows de n8n en un contenedor desechable.
  - Terminal (+1): `MSYS_NO_PATHCONV` para que Git Bash no reescriba rutas al llamar a Docker.
- Ejemplos y notas nuevas en 7 comandos existentes: `ss -tulnp` (lectura de Local Address), zonas de
  firewalld con Docker, ShellCheck `-f gcc` (SC2164, SC2015), bit de ejecución en git como paso de CI y
  `sshd -T` (en sshd gana el primer valor leído: drop-in `00-`).

### Corregido
- «Crear y activar swap» y «Crear memoria swap en un VPS pequeño» se contradecían sobre `fallocate` en XFS:
  ambos usan ahora `dd` como camino principal, como recomienda `man swapon` para XFS y ext4.

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

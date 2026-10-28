# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/); versionado semántico.

## [Sin publicar]

## [1.2.2] — 28 de octubre de 2026

### Agregado
- **Tercer lote de la bandeja** (59 entradas anotadas por otras sesiones entre el 22 y el 28 de octubre:
  `vps`, `vps-infra`, `liveops-dossiers`, `CmdVault`, POO y Comunicación): **44 comandos nuevos** y
  **15 que enriquecen comandos existentes** con ejemplos y notas. El total pasa de 1.575 a **1.619 comandos**
  y de 4.252 a **4.345 ejemplos**.
  - Windows (+12): lanzadores `.bat` (`start /b` con log, candado con handle de archivo, `for /f` con
    ejecutables entre comillas, conhost para probar la X), procesos por línea de comandos con CIM, puertos de
    un PID y `CloseMainWindow()`, Inno Setup con defines, Word por COM a PDF, y tres trampas de PowerShell 5.1
    (comas que arman arreglos, BOM en el pipe a programas nativos, `--jq` con comillas dobles).
  - Docker (+10): API de un contenedor con `urllib`, override de Compose como JSON, rebuild de un solo
    servicio con `--wait`, memoria `anon` vs caché de varios contenedores, tamaño de una imagen en GHCR sin
    descargarla, n8n por CLI (importar credenciales, publicar y ejecutar workflows, revisar una credencial sin
    mostrar el secreto) y Ant de NetBeans dentro de un contenedor.
  - Terminal (+6), Cloud/gcloud (+5: llaves de cuentas de servicio, impersonación sin llaves,
    `generateAccessToken`, Drive y Sheets con curl), Git (+4: actionlint en Docker, `ls-files --eol`, peso de
    lo versionado y de la base de objetos), Python (+3), VPS (+3) y PostgreSQL (+1).

### Cambiado
- Enriquecidos, entre otros: «Etiquetar una versión» (tag retroactivo), «Ver un commit» (`--no-patch`),
  «Revisar y mergear PRs» (merge solo con el CI en verde), «Autenticar GitHub CLI» (WSL), «Proyectos y APIs»,
  «Listar imágenes» (containerd) y «Probar workflows de n8n en un contenedor desechable».
- Secciones y roadmaps de la bandeja fuera del contrato se mapearon a los existentes (p. ej. `bash/curl` →
  Terminal · JSON y YAML; `Automatización` → DevOps). Cuentas y usuarios reales se generalizaron.
### Corregido
- **Jenkinsfile**: el proyecto de Compose, la red y el sidecar de Postgres de cada build se llamaban
  `cmdvault-ci-<n.º de build>`, así que el build #1 de una rama chocaba con restos del #1 de otro job
  (`container is marked for removal and cannot be started` en «Build + smoke»). Ahora el nombre incluye el job
  y la rama: `ci-<job>-<rama>-<build>`.

### Dependencias
- PRs de Dependabot #5 y #6, mergeados antes de esta versión, mergeados antes de esta versión): FastAPI 0.143.3 → 0.156.1,
  SQLAlchemy 2.1.4 → 2.1.5 y pydantic-settings 2.16.0 → 2.16.1 (backend y frontend).

## [1.2.1] — 22 de octubre de 2026

### Agregado
- **Windows Server, GPO avanzadas e IPv6** (+9 comandos y +18 ejemplos en `windows-server.json`, que pasa a 46
  comandos; el entorno Windows queda en 156 y el total en 1.575 comandos y 4.252 ejemplos), siguiendo la guía
  actualizada de la Eva3:
  - Imagen base: quitar IPv6 del adaptador (`Disable-NetAdapterBinding ms_tcpip6`).
  - GPO: Exigido, bloquear herencia, deshabilitar y ordenar vínculos (B5.6); `New-GPLink`/`Copy-GPO`/
    `Rename-GPO`/`Remove-GPO`; `Backup-GPO`/`Restore-GPO`; `Get-GPResultantSetOfPolicy`; script de sesión en
    NETLOGON con `net use` (B5.7); GPO de firewall con `Open-NetGPO`/`Save-NetGPO`; GPO de RDP con NLA y una
    entrada de teoría (LSDOU, herencia, Exigido, filtrado).

### Cambiado
- Ejemplos de Windows Server sincronizados con la guía: A2 con IPv6 desactivado y variante /16
  (255.255.0.0, Red NAT `172.168.0.0/16`), OU con tildes (`Informática`, `Mantención`) en B3, B5.3 y B6, y el
  plan C ya no recomienda guardar la guía dentro de la VM.

## [1.2.0] — 22 de octubre de 2026

### Agregado
- **Sección «Windows Server»** en el entorno Windows (`windows-server.json`): 37 comandos y 63 ejemplos de la
  guía de la Evaluación 3 (Windows Server 2016), con bloques completos listos para copiar y pegar dentro de la
  VM. Etiquetados con `eva3` y `examen` para encontrarlos al buscar. El entorno Windows pasa a 145 comandos y el
  total a 1.547 comandos y 4.184 ejemplos (antes de la bandeja, abajo).
  - Eva3 · Imagen base (+7): nombre, IP fija y DNS (A2), reenviadores, ping, Firefox con TLS 1.2, seguridad
    mejorada de IE, cambio de IP el día de la prueba (A6) y comprobación.
  - Eva3 · VirtualBox (+4): Red NAT `Eva3`, `modifyvm --nic1 natnetwork`, instantáneas y export/import `.ova`.
  - Active Directory (+6): variables B0, promoción con `Install-ADDSForest`, bloque masivo de OU, grupos,
    usuarios y horarios (B3), comandos sueltos, protección de OU y comprobaciones.
  - DNS (+4), DHCP (+4), GPO (+8: recursos compartidos, GPO general, por departamento, política de
    contraseñas, USB/pantalla/Windows Update, filtrado de seguridad, informes y `gpresult`) y Comprobación y
    diagnóstico (+4: cliente al dominio, `dcdiag`, roles y checklist final).
- **Segunda importación de la bandeja** (24 entradas de `all_in_django`, `LiveOps_Core`, `vps`,
  `ConsultaBasesDatos` y del propio despliegue de CmdVault): 19 comandos nuevos y 5 existentes enriquecidos —
  total **1.566 comandos y 4.234 ejemplos**.
  - Git (+5): clonar un tag para producción, clon `--no-local` para reproducir el CI, mover commits de `main`
    a una rama (GitHub Flow), protección de rama y alertas de Dependabot con `gh api`.
  - Python (+4): `pytest -m "not …" --collect-only`, plugins con `-p`, `playwright install chromium` y
    `pip list --format=freeze` para fijar versiones.
  - Docker (+3): `ports: !reset []` en un override, versión real de una imagen `:latest` y memoria `anon` vs
    caché de archivos en el cgroup.
  - Linux (+2): sección de una versión del CHANGELOG con `awk` y `read -rsp` para secretos sin eco.
  - VPS (+2): servicio detrás de un Traefik existente con HTTPS y basic auth, y hash `apr1` sin pasar por
    pantalla.
  - Windows (+2): validar la sintaxis de un `.ps1` con el parser y ocupar un puerto TCP para pruebas.
  - MySQL (+1): importar un `.sql` a MySQL en Docker desde PowerShell 5.1.
  - Enriquecidos: «Publicar una release» (`--verify-tag --latest=false`), «Ver los runs de GitHub Actions»
    (etiquetas publicadas en GHCR), «Llamar a la API de GitHub» (ruta sin `/` en Git Bash), «Etiquetar una
    versión» (`git tag -n`) y «Terminar procesos con taskkill» (`/T` y el `python.exe` lanzador del venv).
- **`.github/workflows/release.yml`**: al pushear un tag `vX.Y.Z` verifica que coincide con
  `backend/pyproject.toml` y con una sección del CHANGELOG, y publica la GitHub Release con esas notas.

### Corregido
- `lint-iac.sh` reintenta hasta 3 veces la descarga de colecciones de Ansible Galaxy: un corte TLS de Galaxy
  dejó en rojo un build de Jenkins sin cambios en el código.

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

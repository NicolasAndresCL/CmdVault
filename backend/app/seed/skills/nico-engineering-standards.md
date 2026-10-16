---
name: nico-engineering-standards
description: >
  Estándares de ingeniería probados en producción de Nicolás Cano Leal (backend
  Python, automatización, data, DevOps/IaC). Contiene su stack por defecto, patrones
  de arquitectura, patrones de refactorización, flujos de trabajo Git/CI, disciplina
  de testing y principios de mejora continua, destilados de Jaime (LiveOps Engine),
  All in Django y su portafolio. USAR SIEMPRE que se inicie, diseñe, refactorice o
  revise cualquier proyecto de Nico — aunque no lo pida explícitamente — para aplicar
  sus convenciones en vez de reinventarlas. Aplica a: arranque de proyecto nuevo,
  decisiones de arquitectura, migraciones, elección de stack, setup de tests/CI,
  hardening de producción, y optimización de rendimiento.
---

# Estándares de ingeniería — Nicolás Cano Leal

> Playbook reutilizable. Cada regla acá **ya se pagó en producción** (Jaime, All in
> Django, portafolio). El objetivo: que cada proyecto nuevo herede estos patrones desde
> el día 1, en vez de redescubrirlos. No es teoría — es lo que funcionó.

---

## 0. Cómo usar este archivo

Al empezar o trabajar un proyecto, recorré las secciones en este orden mental:
**arquitectura → stack → workflow → testing/CI → hardening**, y al final aplicá los
**principios de mejora continua** (sección 7) como filtro sobre cada decisión. La
sección 8 es un checklist de arranque que operacionaliza todo lo anterior.

Principio rector: **separar la lógica de negocio de los efectos secundarios**, testear
la lógica pura sin I/O, y tratar la **resiliencia como requisito, no como extra**.

---

## 1. Stack por defecto (probado, no aspiracional)

Alcanza para el 90% de los proyectos. No agregar tecnología sin una razón concreta.

- **Lenguaje/runtime:** Python 3.12+ · un venv por proyecto.
- **Backend/API:** Django + Django REST Framework (ViewSets, router, paginación,
  exception handler). FastAPI o Flask cuando el proyecto es chico o necesita async.
- **Config:** `pydantic-settings` — settings tipados y validados desde `.env`. Nunca
  hardcodear config ni secretos.
- **BD:** PostgreSQL en producción (vía `dj-database-url` + `psycopg` v3), SQLite por
  defecto/tests. `SQLAlchemy` fuera de Django.
- **Servido producción:** `gunicorn` + `WhiteNoise` (estáticos), endpoint `/healthz/`.
- **Data/ETL:** `pandas` (el caballo de batalla), `openpyxl`/Excel, BigQuery cuando hay
  warehouse. PySpark solo si el volumen lo justifica de verdad.
- **Scraping/automatización:** Selenium (headless, perfiles clonados, resolución offline
  de chromedriver), n8n para glue/integraciones desechables, Playwright si aplica.
- **UI:** NiceGUI (web local en ventana nativa) o Streamlit (dashboards/cliente HTTP).
  CustomTkinter solo si hace falta escritorio puro.
- **Dataviz:** matplotlib + plottable, paletas CVD-safe (Okabe-Ito). Plotly en UI web.
- **DevOps/IaC:** Docker (multi-stage, no-root) + Compose · GitHub Actions (CI) · Jenkins
  · Terraform (AWS EC2/RDS) · Helm/Kubernetes.
- **Calidad:** pytest (+ django/cov), coverage.py, `unittest.mock`, `responses`.

---

## 2. Arquitectura (los patrones que sostienen todo)

### 2.1 Separación de responsabilidades — la decisión más importante
```
core/*_service.py    → LÓGICA PURA (sin red/BD/Selenium) → 100% testeable
data/*_repository.py  → acceso a datos (Sheets/BQ/ORM) · "NUNCA LANZA"
automation/, scraping → efectos secundarios (Selenium) AISLADOS
reporting/            → texto + imágenes, puro sobre DataFrames
ui/                   → orquestación + presentación (cablea todo)
```
La regla de oro: **la decisión de negocio debe poder testearse sin abrir un navegador
ni tocar una red.** Si un test necesita I/O real, la lógica está en la capa equivocada.

### 2.2 Capas de datos "nunca lanzan"
Una integración externa caída (Sheets, Slack, BQ) **no puede tumbar la operación**. Los
repositorios capturan y devuelven vacío/None con log; la lógica de negocio decide qué
hacer con eso. Falla degradada, no caída total.

### 2.3 Engines / schedulers concurrentes
Cada dominio es un **manager** en su propio hilo que dispara un "ciclo" inyectable:
- **Callbacks inyectables**: el manager no conoce el controller; la UI le inyecta el
  ciclo y el logger. Desacople total.
- **Locks non-blocking** para no encolar ciclos que se pisan.
- **Singletons thread-safe persistidos** con **reserva atómica** para cerrar carreras
  check-then-act (ej: cooldown compartido entre motores).
- **Heartbeats + watchdogs**: hilos que **nunca mueren** (outer try/except en todo loop
  de background).

### 2.4 Núcleo agnóstico de framework
Antes de acoplar a una UI/framework, extraé un núcleo (`app_state` +
`orchestrator`) que **no dependa del framework**. Permite cambiar de UI (o correr dos a
la vez) sin reescribir la lógica. Probado en la migración CTk→NiceGUI de Jaime.

### 2.5 Resiliencia como requisito
Asumí el fallo desde el diseño: outer try/except en background, auto-reparación de
dependencias (chromedriver offline), **centinela de sesión** (falla ruidosa, no
silenciosa), y **anti-duplicidad** entre operadores (heartbeat en fuente compartida).

---

## 3. Patrones de refactorización

- **Heredar y evolucionar, no reescribir a ciegas.** Entender el código ajeno primero;
  documentar la arquitectura que no existía; recién ahí evolucionar.
- **Strangler-fig / migración por fases con flag de convivencia.** Nunca big-bang en un
  sistema vivo. La versión vieja sigue 100% operativa hasta alcanzar **paridad**
  verificada. Objetivo: **cero downtime** para los usuarios. (Migración de UI de Jaime.)
- **Extraer el núcleo agnóstico ANTES de cambiar el framework** (ver 2.4).
- **Lectura por estado canónico**, no por variantes de status: normalizar antes de
  filtrar, para no perder datos por strings inconsistentes.
- **Medir antes de refactorizar por rendimiento** (ver 7.1).

---

## 4. Flujo de trabajo Git + DevOps

- **Conventional commits** con cuerpo detallado (qué, por qué, no solo qué).
- **Reproducí CI localmente antes de pushear.** Verificá en un **venv limpio** que la
  suite corre con las dependencias declaradas — no confíes en lo que quedó instalado "de
  rebote" en local. (El bug de plotly ausente en `requirements-dev` se caza así.)
- **`.gitignore` desde el primer commit**: `.env`, `db.sqlite3`, fixtures, credenciales,
  `CLAUDE.md`. Secretos y datos personales **nunca** entran al control de versiones.
- **IaC de punta a punta**: Docker multi-stage no-root + Compose (con healthchecks) +
  GitHub Actions (test + cobertura + build) + Terraform + Helm.
- **Herramienta adecuada a la tarea** (ver 7.4): no quemar un modelo premium en un fix de
  `.bat`; usar el fallback local (Ollama/qwen2.5-coder) para tareas baratas.

---

## 5. Testing y calidad

- **pytest como disciplina, no como trámite.** Foco en **lógica pura sin I/O**.
- **Capas de test claras**: `unittest.mock` para aislar de BD/archivos · `responses`
  para mockear HTTP del lado cliente · smoke/`AppTest` para vistas.
- **Smoke de render** en UIs: ejecutar cada vista para cazar errores antes de que lleguen
  al usuario.
- **Cobertura objetivo ~83%+**, y **100% en los caminos críticos** (serializers, lógica
  de negocio, cálculos).
- **`conftest` fuerza SQLite en tests** aunque producción sea Postgres — separar entorno
  de test de entorno de producción.
- **REGLA FIRME (gap histórico a cerrar siempre): CI en verde en cada push.** Todo
  proyecto — incluidos los internos/de escritorio como Jaime — debe tener su suite
  corriendo en GitHub Actions. "Tests que corro a mano" no cuenta como red de seguridad.

---

## 6. Hardening de producción (checklist, no opcional)

Antes de considerar algo "listo para producción":

- [ ] **Autenticación** en la API (Token/JWT + `IsAuthenticated`), nada de `AllowAny`.
- [ ] **Rate limiting** diferenciado (anon / user / token) — pensarlo como perfiles de
      riesgo, no como un número al azar.
- [ ] **`manage.py check --deploy` limpio**: SSL redirect, HSTS, cookies secure
      (togglear con `SECURE_HTTPS`).
- [ ] **Validación de `SECRET_KEY` fuerte**; secretos fuera del código.
- [ ] **Gestión de secretos en K8s** con SealedSecrets/SOPS (no `--set` en claro).
- [ ] **Postgres gestionado** (RDS) sobre StatefulSet propio en producción real.
- [ ] **Estado de Terraform en backend remoto** (S3 + DynamoDB lock) para trabajo en
      equipo — el state local se rompe apenas hay más de una persona.
- [ ] **Backups** de BD + verificación de restauración.
- [ ] **Observabilidad básica**: logs estructurados, métricas, healthchecks externos.

---

## 7. Principios de mejora continua (el filtro sobre cada decisión)

### 7.1 Medir antes de optimizar
Encontrar el cuello de botella **real** con datos, no asumirlo. (De ~37 min a ~10 min al
entender que el costo era el cooldown de la plataforma, no el código; de 21 llamadas a
Sheets a 1 con un singleton + TTL cache.) Perfilar > adivinar.

### 7.2 Aprender lo que el problema exige, cuando lo exige
No estudiar en abstracto: cuando el problema pide BigQuery, DOM reverse-engineering o
reserva atómica, aprender eso, a fondo, y aplicarlo. El proyecto dicta el currículum.

### 7.3 Metabolizar los fracasos
Un proyecto archivado deja una lección, no solo un repo muerto. (El hub que causaba
triple reasignación → regla "una cuenta = una automatización a la vez" → reuso correcto
de NiceGUI después.) Documentar el porqué del archivado.

### 7.4 Herramienta adecuada al costo de la tarea
No usar capacidad premium en trabajo de baja complejidad. Modelo/entorno local para glue
y fixes; reservar lo caro para lo que de verdad lo necesita. Dar el **error real** en vez
de dejar que la herramienta adivine a ciegas (rompe el loop de reintentos).

### 7.5 Traducir negocio → features probadas
Los pedidos llegan como necesidad de negocio ("no notifiquen a los caminantes"), no como
ticket técnico. Mapear el problema, decidir el enfoque, entregarlo **testeado**.

### 7.6 Métricas honestas y consistentes
Números reales, verificables, y **coherentes en todo el documento** (si la suite tiene
548 tests, no aparece "503" en otra sección). La precisión es la credibilidad; un dato
inconsistente resta justo donde uno es más fuerte. No inflar — ni el trabajo ni el CV.

---

## 8. Checklist de arranque de proyecto (día 1)

1. `venv` + `pydantic-settings` con `.env` tipado.
2. Estructura en capas (sección 2.1): `core/` · `data/` · `services` · `ui/`.
3. `.gitignore` con secretos/datos fuera + primer commit convencional.
4. pytest configurado + `conftest` (SQLite en tests) + primer test de lógica pura.
5. Dockerfile multi-stage no-root + Compose con healthchecks + `/healthz/`.
6. **GitHub Actions desde el inicio** (test + cobertura + build) — no dejarlo "para
   después".
7. Postgres vía `DATABASE_URL` con fallback SQLite.
8. Si va a producción: recorrer el checklist de hardening (sección 6).
9. Aplicar el filtro de mejora continua (sección 7) en cada decisión.

---

*Origen: patrones extraídos de Jaime (LiveOps Engine, v4.0→v6.0, 548 tests, ~10 engines
concurrentes, migración de UI zero-downtime), All in Django (IaC completa, CI verde, API
autenticada, 130 tests) y el portafolio. Autor: Nicolás Andrés Cano Leal.*

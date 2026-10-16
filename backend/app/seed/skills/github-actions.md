---
name: github-actions
description: >
  Estándares de CI/CD de Nicolás Cano Leal con GitHub Actions: reproducir el
  pipeline en local ANTES de commitear, jobs en cascada
  (lint→test→build), servicios de base de datos, permisos mínimos y
  verificación real de hardening de producción. USAR SIEMPRE que se cree o
  edite un workflow en `.github/workflows/`, se diseñe un pipeline de CI/CD,
  o se arranque un repositorio nuevo — todo repo nace con CI en el primer
  commit, no se agrega "cuando el proyecto crezca".
---

# GitHub Actions — estándares de Nicolás Cano Leal

> Referencia real y probada: `backend/.github/workflows/tests.yml` de
> TienditaMarian (3 jobs: `test`, `test-postgres`, `deploy-check`).

## Regla rectora

**El CI mínimo verifica que el proyecto CONSTRUYE y ARRANCA, no solo que
lintea.** Un pipeline que únicamente corre un linter da falsa seguridad — los
fallos reales aparecen al construir, migrar y levantar el servicio. Un
"CI en verde" que solo comprobó estilo no es una red de seguridad real.

## Orden de jobs (rápido → lento)

No gastar minutos de build en algo que un linter de un minuto ya descarta:

1. **Lint/formato/tipos** (segundos): `ruff check .`
2. **Tests + cobertura** (con `--cov-fail-under`, no solo imprimir el número)
3. **Build** (Docker, si aplica)
4. **Verificación de hardening de despliegue** (`check --deploy` en Django)

## Servicios de base de datos en CI

Cuando la lógica depende de comportamiento específico del motor de producción
(ej. `select_for_update` que SQLite ignora silenciosamente), correr un job
aparte contra el motor real:

```yaml
test-postgres:
  runs-on: ubuntu-latest
  services:
    postgres:
      image: postgres:16-alpine
      env:
        POSTGRES_USER: app
        POSTGRES_PASSWORD: app
        POSTGRES_DB: app_test
      ports:
        - 5432:5432
      options: >-
        --health-cmd pg_isready
        --health-interval 10s
        --health-timeout 5s
        --health-retries 5
  env:
    DATABASE_URL: postgres://app:app@localhost:5432/app_test
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: '3.12'
        cache: pip
    - run: pip install -r requirements/dev.txt
    # -rs muestra los skips: si el test de concurrencia apareciera saltado
    # aquí, sería señal de que NO está corriendo contra Postgres de verdad.
    - run: pytest -rs
```

## Verificar hardening real, no solo que compile

Un job `deploy-check` que corre `manage.py check --deploy --fail-level
WARNING` contra la config de producción (SSL redirect, HSTS, cookies secure,
fortaleza de `SECRET_KEY`) evita que un settings inseguro llegue a producción
sin que nadie se entere:

```yaml
deploy-check:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with: { python-version: '3.12', cache: pip }
    - run: pip install -r requirements/prod.txt
    - name: check --deploy
      env:
        DJANGO_SETTINGS_MODULE: config.settings.prod
        ALLOWED_HOSTS: miapp.com
        DATABASE_URL: sqlite:///db.sqlite3
        SECURE_HTTPS: 'True'
      run: |
        export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(64))')"
        python manage.py check --deploy --fail-level WARNING
```

## Un CI en verde no significa que esté haciendo lo que crees

Dos formas de tener un pipeline verde que no verifica nada:

**1. La herramienta configurada mal, en silencio.** Al integrar Trivy, el informe
SARIF se estaba generando con TODAS las severidades pese a declarar
`severity: CRITICAL,HIGH,MEDIUM`: falta el input `limit-severities-for-sarif:
true`, que **solo aparece en el `action.yaml` de la action, no en su README**.
El CI pasaba, el informe existía, y contradecía en silencio lo que la propia
documentación del proyecto afirmaba.

> **Contrastar la configuración de una herramienta con su fuente**, no con la
> memoria ni con el primer ejemplo de un blog: leer su `action.yaml`, comprobar
> sus releases reales. La misma revisión destapó que la action estaba fijada
> ocho meses por detrás de la versión actual.

**2. La verificación probada solo en el caso bueno.** Un chequeo de hardening
que buscaba puertos expuestos con el patrón `"[0-9]` marcaba también
`"127.0.0.1:6080:6080"`, porque una IP empieza por dígito. Habría dejado el CI en
rojo permanente hasta que alguien lo silenciara — el peor final posible para una
comprobación de seguridad.

> **Una verificación que solo se prueba en el caso bueno no está probada.**
> Toda comprobación nueva se valida en los DOS sentidos: que no marque lo
> correcto, y que **sí** detecte lo que dice detectar. Introducir el fallo a
> propósito y comprobar que salta, antes de confiar en ella.

## Verificar en verde ANTES de commitear

**Si la tarea tocó código, tests o refactorizaciones, se corre lo mismo que corre
el CI antes de armar un solo commit.** No una parte: todo. Si algo falla, se
corrige primero. Ver [[cierre-de-tarea]] §2.

**Por qué, con un caso real.** En TienditaMarian hubo **tres corridas seguidas en
rojo** sin que nadie se enterara. En local se ejecutaban `pytest` y `ruff`, ambos
en verde; el job que fallaba era `backend-deploy-check`
(`check --deploy --fail-level WARNING`) — **el único que no se reproducía a
mano**. Los warnings venían de drf-spectacular: una clase de autenticación propia
que no sabía describir, y una vista sin serializer. Ninguno aparecía en la suite.

Un `scripts/verificar.sh` que recorra los jobs en el mismo orden del workflow:

```bash
#!/usr/bin/env bash
set -uo pipefail
fallos=0
ejecutar() {              # <descripcion> <comando...>
  local desc="$1"; shift
  if "$@" > /tmp/verificar.log 2>&1; then
    echo "  ✔ $desc"
  else
    echo "  ✖ $desc"; tail -25 /tmp/verificar.log | sed 's/^/    /'
    fallos=$((fallos + 1))
  fi
}

ejecutar "ruff"      "$PY" -m ruff check .
ejecutar "tests"     "$PY" -m pytest -q --cov --cov-fail-under=90
# El que se olvida SIEMPRE: corre con el settings de PRODUCCIÓN y una clave
# efímera, porque `check --deploy` rechaza claves débiles y fallaría por eso.
ejecutar "hardening" "$PY" manage.py check --deploy --fail-level WARNING
ejecutar "front"     npm run lint

[ "$fallos" -eq 0 ] && echo "Todo en verde." || { echo "NO pushees todavía."; exit 1; }
```

Los jobs que más se olvidan: **hardening de producción** (corre con otro
settings), **umbral de cobertura** (no basta con que los tests pasen), **build**
(no solo lint) y los que usan el **motor real** en vez del de desarrollo.

### Mejor aún: que falle dentro de la suite

Un script hay que acordarse de ejecutarlo; un test corre siempre. Cuando la
condición que rompe el CI se pueda comprobar en código, escríbela como test:

```python
def test_el_esquema_se_genera_sin_un_solo_warning():
    """El CI trata los warnings de drf-spectacular como fallo del build."""
    from drf_spectacular.drainage import GENERATOR_STATS

    GENERATOR_STATS.reset()
    with GENERATOR_STATS.silence():
        SchemaGenerator().get_schema(request=None, public=True)
    assert not list(GENERATOR_STATS._warn_cache)
```

Eso adelanta el fallo de un job lento y remoto a la suite rápida y local.

### `act` para lo que el script no puede imitar

Cuando el job usa matrices, servicios, permisos o `GITHUB_TOKEN`,
[`act`](https://github.com/nektos/act) ejecuta los workflows de verdad en Docker:

```bash
act --list                    # qué correría
act -j backend-deploy-check   # un job concreto
```

No sustituye al script (es mucho más lento y no reproduce el runner al 100 %),
pero cubre lo que el script no.

### Y después del push, mirar el run

```bash
gh run list --limit 3
gh run view <id> --log-failed
```

Verificar el resultado es parte de pushear. **Un pipeline que avisa y nadie mira
no sirve de nada**: los tres rojos de arriba estuvieron visibles todo el tiempo.

## Lo obligatorio se automatiza, no se anota

Si algo "hay que acordarse de hacer antes de pushear", **no es un recordatorio,
es un hook**. Una regla escrita en un documento es el mismo mecanismo que ya
falló: depende de que alguien la recuerde en el momento justo.

Un `verificar.sh` que reproduce el job de lint completo, más
`.githooks/pre-commit` que lo invoca solo cuando el commit toca los archivos
relevantes, y `git config core.hooksPath .githooks` para activarlo. El hook debe
filtrar por archivos tocados: un commit de documentación no debe esperar a que
arranquen tres contenedores.

> **Un paso obligatorio que se puede omitir sin que pase nada, no es
> obligatorio.**

## Reglas de higiene

- **Permisos mínimos**: no declarar `permissions` deja el default heredado del
  repo (a veces `write` global). Declarar `contents: read` explícito y ampliar
  solo en el job que de verdad necesita más (ej. `packages: write` para
  publicar una imagen).
- **`GITHUB_TOKEN` del workflow antes que crear PATs.** Un PAT personal en
  secrets es una llave que sobrevive a quien la creó y no se audita igual.
- **Cache de dependencias** (`cache: pip` en `setup-python`, o
  `actions/cache` genérico) para no reinstalar todo en cada push.
- **`.env` fuera del checkout de CI**: el settings de test debe inyectar sus
  propios defaults (SQLite en memoria, correo `locmem`) para que la suite
  corra en un checkout limpio, sin secretos ni `.env` presentes — así es como
  corre en CI de verdad.
- **Cobertura como condición de fallo**, no como métrica decorativa:
  `pytest --cov --cov-report=term-missing --cov-fail-under=70` (ajustar el
  umbral al target del proyecto — objetivo ~83%+ y 100% en caminos críticos).
- **Dependabot + plantillas de issue/PR + badge de CI en el README** son parte
  de la higiene mínima de cualquier repo nuevo, no un "nice to have" tardío.
- **Reproducir CI en local antes de pushear**, en un venv limpio — no confiar
  en lo que quedó instalado "de rebote" (así se caza el típico "faltaba
  `plotly` en requirements-dev" que solo revienta en CI).

## Trampas conocidas

- Declarar `DB_USER`/`DB_PASSWORD` sueltos que nadie lee porque el settings ya
  arma todo desde `DATABASE_URL` — limpiar env vars muertas del workflow.
- Job de Postgres que "pasa" porque el test de concurrencia se saltó
  silenciosamente: usar `-rs` (o equivalente) para que los skips sean
  visibles en el log de CI.
- `check --deploy` sin `SECRET_KEY` fuerte falla por la clave, no por el
  hardening real — generar una clave efímera solo para el check, que nunca
  sirve tráfico.

## Ver también
[[docker]] para el job de build de imagen · [[python-backend]] para lo que el
pipeline está verificando · [[jenkins]] como alternativa cuando el pipeline
necesita orquestar despliegues on-prem o infraestructura propia ·
[[terraform]] para el job de `plan`/`apply` con aprobación humana ·
[[kubernetes]] para el `rollout` que cierra el pipeline.

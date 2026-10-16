---
name: jenkins
description: >
  Estándares de Nicolás Cano Leal para pipelines Jenkins declarativos:
  agentes efímeros vía Docker, credenciales fuera del Jenkinsfile, stages en
  cascada rápido→lento y el mismo rigor de hardening que en GitHub Actions.
  USAR SIEMPRE que se cree o edite un `Jenkinsfile`, se configure un job de
  Jenkins, se levante o migre un controller Jenkins en Docker (dónde vive
  `JENKINS_HOME`, arranque lento, respaldo), o se decida entre Jenkins y GitHub
  Actions para un pipeline nuevo.
---

# Jenkins — estándares de Nicolás Cano Leal

> Mismo filtro de calidad que [[github-actions]]: el pipeline verifica que el
> proyecto CONSTRUYE y ARRANCA, no solo que lintea. Jenkins entra cuando hace
> falta orquestar infraestructura propia (agentes on-prem, despliegue a un
> servidor que no es GitHub-hosted, integración con Docker/K8s internos) que
> GitHub Actions no cubre bien o sale caro en minutos de runner hosted.

## Cuándo Jenkins y no GitHub Actions

- El despliegue final vive **on-prem** o en infraestructura propia sin buena
  integración nativa con Actions.
- Se necesita un agente con acceso a red interna (VPN, DB privada) que un
  runner hosted no puede alcanzar.
- El repo ya vive en un ecosistema con Jenkins establecido (no reinventar
  tooling de CI en un monorepo que ya lo tiene resuelto).

Si nada de eso aplica, preferir [[github-actions]]: menos infraestructura que
mantener.

## Pipeline declarativo — esqueleto base

```groovy
pipeline {
    agent {
        docker { image 'python:3.12-slim' }  // agente efímero, reproducible:
        // no depender del estado acumulado de un agente Jenkins persistente.
    }

    options {
        timeout(time: 15, unit: 'MINUTES')  // ningún job cuelga para siempre
        disableConcurrentBuilds()           // evita builds pisándose la BD de test
    }

    environment {
        DJANGO_SETTINGS_MODULE = 'config.settings.test'
        // Nunca credenciales en claro aquí. Ver sección de credenciales.
    }

    stages {
        stage('Lint') {
            steps { sh 'pip install -q -r requirements/dev.txt && ruff check .' }
        }
        stage('Test + cobertura') {
            steps {
                sh 'pytest --cov --cov-report=term-missing --cov-fail-under=70'
            }
        }
        stage('Build imagen') {
            when { branch 'main' }
            steps { sh 'docker build -t miapp:${GIT_COMMIT} .' }
        }
        stage('Deploy check') {
            when { branch 'main' }
            steps {
                withCredentials([string(credentialsId: 'secret-key-efimera', variable: 'SECRET_KEY')]) {
                    sh 'python manage.py check --deploy --fail-level WARNING'
                }
            }
        }
    }

    post {
        always { junit '**/test-results/*.xml' }
        failure { echo 'Build falló — revisar log del stage que rompió, no reintentar a ciegas.' }
    }
}
```

## Reglas no negociables

1. **Orden rápido → lento**: lint antes que tests, tests antes que build de
   imagen, build antes que deploy check. No gastar minutos de agente en un
   build que un `ruff check` de segundos ya iba a rechazar.
2. **Credenciales SIEMPRE vía el credential store de Jenkins**
   (`withCredentials`, `credentials()`), nunca en texto plano en el
   `Jenkinsfile` ni en variables de entorno globales del job. El `Jenkinsfile`
   vive en el repo — cualquier secreto ahí es un secreto filtrado.
3. **Agentes Docker efímeros** en vez de agentes persistentes con estado
   acumulado: reproducibilidad — el build de hoy corre en el mismo entorno
   limpio que el de mañana, sin "funciona en mi agente".
4. **`timeout()` en cada pipeline.** Un job colgado indefinidamente bloquea el
   executor para todo lo demás.
5. **`disableConcurrentBuilds()`** cuando el pipeline toca una BD/recurso
   compartido de test — dos builds concurrentes contra la misma base
   corrompen resultados sin avisar.
6. **Verificar hardening real de despliegue**, igual que en GitHub Actions
   (`check --deploy` u equivalente del framework) — no basta con que el build
   compile.
7. **Notificación en fallo con contexto útil**: qué stage rompió y el log
   relevante, no un "build failed" genérico que obliga a entrar a la UI.

## El controller en Docker (Docker Desktop)

> Referencia real: `C:\dev\projects\jenkins\` (compose, `Dockerfile`,
> `respaldo.ps1`, `pasos.md`). Copiar el patrón.

1. **`JENKINS_HOME` en un volumen nombrado, nunca en un bind mount de
   Windows.** Jenkins abre todos los plugins y sus clases al arrancar; con
   4.599 ficheros a través de la capa VM ↔ NTFS de Docker Desktop el arranque
   medía **7–11 min** (~9 en `Listed all plugins`). En volumen: **5–7 s**.
   Detalle y reglas en [[docker]], sección *Almacenamiento*.
2. **Bind mount solo de lo que se edita desde el host, montado encima del
   volumen**: `init.groovy.d/` (configuración como código), la carpeta de
   fuentes de secretos que leen esos scripts, y un buzón de ficheros de entrada
   si algún job lo necesita. Lo demás se lee con `docker exec` / `docker cp`.
   ```yaml
   volumes:
     - jenkins_home:/var/jenkins_home
     - C:/Users/<u>/jenkins_home/init.groovy.d:/var/jenkins_home/init.groovy.d
     - C:/Users/<u>/jenkins_home/secretos:/var/jenkins_home/secretos
     - //var/run/docker.sock:/var/run/docker.sock
   volumes:
     jenkins_home:
       external: true      # creado a mano; `compose down -v` no lo alcanza
   ```
3. **Imagen propia sobre la oficial fijada** (`jenkins/jenkins:<x.y.z>-lts-jdk17`,
   nunca `lts` a secas: cambia de JDK sin avisar y rompe plugins). La oficial
   no trae el cliente `docker`; con el socket montado y sin binario, todo
   `sh 'docker ...'` muere con `docker: not found`.
4. **Healthcheck contra `/login` con `start_period` medido**, no copiado:
   2 min sobre volumen (margen ×15 sobre 5–7 s); eran 15 min sobre bind mount.
   Si el arranque vuelve a tardar minutos, lo primero es
   `docker inspect --format '{{json .Mounts}}'`: un compose viejo o un
   contenedor huérfano con el bind mount reproducen el síntoma antiguo.
5. **Respaldo = volumen + carpeta de bind mounts, juntos.** Las credenciales
   cifradas (`secrets/`, `credentials.xml`) están en el volumen; sus ficheros
   fuente, en la carpeta. Uno sin el otro deja credenciales ilegibles o
   scripts de arranque sin entrada. Exportar el volumen desde `alpine` + `tar`
   con Jenkins parado; el volumen **no sobrevive** a un *Reset* de Docker
   Desktop.
6. **Verificar una migración de `JENKINS_HOME` por la API, con `curl -g`**:
   cuenta de plugins (`pluginManager/api/json?depth=1`), jobs
   (`api/json?tree=jobs[name]`), y sobre todo que una credencial **descifre**
   (`credentials/store/system/domain/_/api/json` lista su `id`) — es la prueba
   de que `secrets/` viajó bien. Sin `-g`, `curl` trata los corchetes como
   *globbing* y devuelve vacío: "0 plugins" cuando están los 92.
7. **`init.groovy.d` idempotente**: cada script comprueba si el job/credencial
   existe y no lo pisa. En el log de arranque deben leerse los "ya existe: no
   se toca" — es a la vez la prueba de idempotencia y de que los scripts ven su
   carpeta de fuentes.

## Trampas conocidas

- **`Listed all plugins` lento = I/O de `JENKINS_HOME`, no la JVM.** Antes de
  tocar `JAVA_OPTS` o subir RAM, mirar dónde está montado `/var/jenkins_home`.
- **Jenkinsfile sin `agent` por stage** hereda el agente global — si el
  `Dockerfile` del proyecto usa una versión de Python distinta a la del
  agente Jenkins por defecto, el build "funciona" pero no representa el
  entorno real de producción. Fijar la imagen del agente explícitamente.
- **Plugins desactualizados** son la fuente #1 de builds rotos sin cambios en
  el código propio — pinnear versiones de plugins críticos cuando el pipeline
  es sensible a regresiones.
- **Webhooks de GitHub mal configurados** hacen que Jenkins no dispare en push
  y el equipo confíe en un CI que no corrió — validar el webhook con un push
  de prueba al configurar el job, no asumir.

## Ver también
[[github-actions]] para el equivalente hosted · [[docker]] para las imágenes
que Jenkins construye o usa como agente · [[terraform]] y [[kubernetes]] para
la infraestructura y el despliegue que estos pipelines orquestan · [[n8n]]
cuando el problema es glue entre servicios, no build/deploy de código propio.

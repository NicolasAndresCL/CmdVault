// CmdVault — pipeline declarativo para el Jenkins local (C:\dev\projects\jenkins).
// Mismo filtro que .github/workflows/ci.yml: lint -> IaC -> tests -> build + smoke,
// más un despliegue opcional al VPS con Ansible que exige aprobación humana.
//
// Hecho para ese controller tal como está: Pipeline + Credentials Binding + SSH Credentials
// + JUnit, cliente docker con el socket del host montado y SIN el plugin Docker Pipeline.
// Por eso cada paso corre en un contenedor efímero con `docker run --rm --volumes-from`:
// JENKINS_HOME es un volumen nombrado y el workspace no existe en el host, así que el
// contenedor del paso hereda los volúmenes del controller y ve la misma ruta.
//
// Credenciales (credential store, nunca en este archivo):
//   cmdvault-vps-ssh        SSH Username with private key  (usuario deploy del VPS)
//   cmdvault-vault-pass     Secret file                     (contraseña de ansible-vault)
//   cmdvault-inventory      Secret file                     (inventory/hosts.yml real)
//   cmdvault-vault-vars     Secret file                     (group_vars/cmdvault/vault.yml cifrado)
//   cmdvault-known-hosts    Secret file                     (ssh-keyscan del VPS, verificado a mano)

def stageFallido = ''

// Ejecuta `comando` (sh -e) en un contenedor efímero que comparte el workspace del controller.
// `comando` no debe contener comillas simples.
def enContenedor(String imagen, String comando, String extra = '') {
    sh """docker run --rm --volumes-from "\$(hostname)" -w "\$WORKSPACE" -e HOME="\$WORKSPACE" \
        -e PIP_NO_CACHE_DIR=1 -e PIP_DISABLE_PIP_VERSION_CHECK=1 -e PYTHONIOENCODING=utf-8 \
        ${extra} ${imagen} sh -ec '${comando}'"""
}

pipeline {
    agent any

    options {
        timeout(time: 40, unit: 'MINUTES')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    parameters {
        booleanParam(name: 'DEPLOY', defaultValue: false,
                     description: 'Desplegar al VPS con Ansible tras el pipeline en verde (pide aprobación).')
        string(name: 'VERSION', defaultValue: 'main',
               description: 'Rama, tag o commit que Ansible despliega (cmdvault_version).')
    }

    environment {
        PY_IMG = 'python:3.14-slim'
        // Único por job + rama + build: con solo BUILD_NUMBER, el #1 de una rama chocaba con restos
        // del #1 de otro job («container is marked for removal», 2026-10-28). Compose exige [a-z0-9_-].
        CI_ID = "ci-${env.JOB_NAME}-${env.BUILD_NUMBER}".toLowerCase().replaceAll('[^a-z0-9]+', '-')
        RED_PG = "${env.CI_ID}-net"
        PG = "${env.CI_ID}-pg"
    }

    stages {
        stage('Lint') {
            steps {
                script {
                    stageFallido = env.STAGE_NAME
                    enContenedor(env.PY_IMG, '''
                        python -m venv .venv-lint
                        .venv-lint/bin/pip install -q ruff==0.17.1 pydantic==2.14.1
                        .venv-lint/bin/ruff check backend frontend
                        .venv-lint/bin/ruff format --check backend frontend
                        cd backend && ../.venv-lint/bin/python -m app.seed.validate
                    ''')
                    // Un .sh creado en Windows entra como 100644 y en Linux da Permission denied.
                    enContenedor('alpine:3.22', '''
                        apk add -q git
                        if git -c safe.directory="*" ls-files -s -- "*.sh" | grep -v "^100755"; then
                            echo "Scripts sin bit de ejecución en git"; exit 1
                        fi
                    ''')
                    // Override de producción detrás de Traefik (compose.traefik.yml): YAML y `!reset` válidos.
                    sh '''
                        POSTGRES_PASSWORD=ci API_KEY=ci STORAGE_SECRET=ci CMDVAULT_HOST=cmdvault.ci.example \
                          TRAEFIK_NETWORK=ci CMDVAULT_BASIC_AUTH=ci:x \
                          docker compose -f docker-compose.yml -f compose.traefik.yml config --quiet
                    '''
                }
            }
        }

        stage('IaC: Terraform + Ansible') {
            environment { DOCKER_VOLUMES_FROM = sh(script: 'hostname', returnStdout: true).trim() }
            steps {
                script { stageFallido = env.STAGE_NAME }
                sh './scripts/lint-iac.sh'
            }
        }

        stage('Tests') {
            parallel {
                stage('Backend (SQLite)') {
                    steps {
                        script {
                            stageFallido = env.STAGE_NAME
                            enContenedor(env.PY_IMG, '''
                                python -m venv .venv && .venv/bin/pip install -q -r backend/requirements-dev.txt
                                cd backend && ../.venv/bin/pytest -rs --cov --cov-fail-under=90 --junitxml=../reports/backend.xml
                            ''')
                        }
                    }
                    post { always { junit allowEmptyResults: true, testResults: 'reports/backend.xml' } }
                }
                stage('Frontend') {
                    steps {
                        script {
                            stageFallido = env.STAGE_NAME
                            enContenedor(env.PY_IMG, '''
                                python -m venv .venv-ui && .venv-ui/bin/pip install -q -r frontend/requirements-dev.txt
                                cd frontend && ../.venv-ui/bin/pytest -rs --cov --cov-fail-under=80 --junitxml=../reports/frontend.xml
                            ''')
                        }
                    }
                    post { always { junit allowEmptyResults: true, testResults: 'reports/frontend.xml' } }
                }
                stage('Backend (Postgres 18)') {
                    steps {
                        script {
                            stageFallido = env.STAGE_NAME
                            // Sidecar efímero en una red propia del build; se elimina en post.
                            sh '''
                                docker network create "$RED_PG"
                                docker run -d --rm --name "$PG" --network "$RED_PG" --network-alias pg \
                                    -e POSTGRES_USER=app -e POSTGRES_PASSWORD=app -e POSTGRES_DB=app_test postgres:18-alpine
                                until docker exec "$PG" pg_isready -U app -d app_test; do sleep 1; done
                            '''
                            enContenedor(env.PY_IMG, '''
                                python -m venv .venv-pg && .venv-pg/bin/pip install -q -r backend/requirements-dev.txt
                                cd backend && ../.venv-pg/bin/pytest -rs
                            ''', "--network ${env.RED_PG} -e TEST_DATABASE_URL=postgresql+psycopg://app:app@pg:5432/app_test")
                        }
                    }
                    post {
                        always { sh 'docker rm -f "$PG" >/dev/null 2>&1 || true; docker network rm "$RED_PG" >/dev/null 2>&1 || true' }
                    }
                }
            }
        }

        stage('Build + smoke') {
            environment {
                // Proyecto y puertos propios por build: no choca con el stack diario ni con el 8080 de Jenkins.
                COMPOSE_PROJECT_NAME = "${env.CI_ID}"
                BACKEND_PORT = '28000'
                FRONTEND_PORT = '28090'
            }
            steps {
                script { stageFallido = env.STAGE_NAME }
                sh '''
                    # Secretos efímeros solo para esta prueba (el entorno del shell gana al .env).
                    export POSTGRES_PASSWORD=$(openssl rand -hex 16)
                    export API_KEY=$(openssl rand -hex 24)
                    export STORAGE_SECRET=$(openssl rand -hex 24)
                    docker compose up -d --build --wait --wait-timeout 180
                '''
                // El smoke corre en la red del stack: desde el controller, "localhost" no es el host.
                enContenedor(env.PY_IMG, '''
                    apt-get update -qq && apt-get install -y -qq curl >/dev/null
                    bash scripts/smoke.sh http://frontend:8080 http://backend:8000
                ''', "--network ${env.COMPOSE_PROJECT_NAME}_default")
            }
            post {
                failure { sh 'docker compose logs --no-color --tail=200 || true' }
                // Norma: lo que se levanta para probar, se baja SIEMPRE.
                always { sh 'docker compose down -v --remove-orphans || true' }
            }
        }

        stage('Deploy al VPS') {
            when {
                allOf { branch 'main'; expression { params.DEPLOY } }
            }
            steps {
                script { stageFallido = env.STAGE_NAME }
                input message: "¿Desplegar ${params.VERSION} al VPS de producción?", ok: 'Desplegar'
                withCredentials([
                    sshUserPrivateKey(credentialsId: 'cmdvault-vps-ssh', keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER'),
                    file(credentialsId: 'cmdvault-vault-pass', variable: 'VAULT_PASS'),
                    file(credentialsId: 'cmdvault-inventory', variable: 'INVENTORY'),
                    file(credentialsId: 'cmdvault-vault-vars', variable: 'VAULT_VARS'),
                    file(credentialsId: 'cmdvault-known-hosts', variable: 'KNOWN_HOSTS'),
                ]) {
                    script {
                        enContenedor(env.PY_IMG, '''
                            apt-get update -qq && apt-get install -y -qq git openssh-client >/dev/null
                            python -m venv .venv-ansible && .venv-ansible/bin/pip install -q ansible-core==2.21.5
                            cd infra/ansible
                            cp "$VAULT_VARS" group_vars/cmdvault/vault.yml
                            ../../.venv-ansible/bin/ansible-galaxy collection install -r requirements.yml -p ./collections
                            ../../.venv-ansible/bin/ansible-playbook -i "$INVENTORY" -u "$SSH_USER" --private-key "$SSH_KEY" \
                                --ssh-common-args "-o UserKnownHostsFile=$KNOWN_HOSTS -o StrictHostKeyChecking=yes" \
                                --vault-password-file "$VAULT_PASS" -e cmdvault_version="$VERSION" playbooks/site.yml
                        ''', '-e SSH_KEY -e SSH_USER -e VAULT_PASS -e INVENTORY -e VAULT_VARS -e KNOWN_HOSTS -e VERSION')
                    }
                }
            }
            post { always { sh 'rm -f infra/ansible/group_vars/cmdvault/vault.yml' } }
        }
    }

    post {
        failure {
            echo "CmdVault #${env.BUILD_NUMBER}: falló el stage «${stageFallido}». Revisar su log, no reintentar a ciegas: ${env.BUILD_URL}console"
        }
        success {
            echo "CmdVault #${env.BUILD_NUMBER} en verde${params.DEPLOY ? ' y desplegado' : ''}."
        }
    }
}

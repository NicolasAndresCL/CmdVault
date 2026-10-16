---
name: kubernetes
description: >
  Estándares de Kubernetes de Nicolás Cano Leal: manifiestos declarativos y
  versionados, probes que distinguen vivo de listo, requests/limits siempre,
  contenedores no-root, secretos fuera del repo y despliegue reproducible con
  Kustomize/Helm. USAR SIEMPRE que se escriba o revise un manifiesto (Deployment,
  Service, Ingress, ConfigMap), se diseñe cómo desplegar un servicio en un
  clúster, o se depure un pod que no arranca — aunque no se pida "sigue mis
  estándares".
---

# Kubernetes — estándares de Nicolás Cano Leal

> K8s orquesta **contenedores que ya existen**: primero [[docker]] produce una
> imagen correcta (multi-stage, no-root, healthcheck), y [[terraform]] crea el
> clúster. Kubernetes solo decide cuántas réplicas corren, dónde y con qué
> configuración. Meter aquí problemas que se resuelven en el Dockerfile es la
> forma más rápida de tener un clúster imposible de depurar.
>
> **Antes de usarlo, preguntarse si hace falta.** Para un servicio único con
> tráfico moderado, Compose sobre una VM o un PaaS resuelve lo mismo con una
> fracción de la complejidad operativa. K8s se justifica con varios servicios,
> escalado real, o un equipo que ya lo opera.

## Stack por defecto

Manifiestos YAML versionados en el repo · **Kustomize** para variar por
entorno (Helm cuando se distribuye a terceros) · `kubectl apply` desde CI,
nunca desde el portátil · `kubeconform`/`kubectl --dry-run=server` para
validar · Secretos desde un gestor externo (External Secrets, Sealed Secrets).

---

## 1. Todo declarativo y versionado — cero `kubectl edit`

**Regla dura: si un cambio no está en el repo, no existe.** Un `kubectl edit
deployment` en caliente se pierde en el siguiente `apply` y deja al clúster en
un estado que nadie puede reproducir. Es el mismo *drift* que en [[terraform]].

- Manifiestos en Git → CI hace `apply`. La persona no toca `kubectl` contra
  producción salvo para **leer** (`get`, `describe`, `logs`).
- **Nunca `latest` en la imagen.** Un pod reiniciado bajaría una imagen
  distinta a la de sus compañeros, y no hay forma de saber qué corre. Usar el
  SHA del commit o un tag inmutable:
  ```yaml
  image: registry/miapp:a1d0925   # el mismo tag que construyó el CI
  ```
- `imagePullPolicy: IfNotPresent` con tags inmutables (con `latest` obliga a
  `Always` y aun así no garantiza nada).

---

## 2. Probes: `liveness` y `readiness` NO son lo mismo

Es el error conceptual más caro, porque configurarlas mal **empeora** las
cosas frente a no tenerlas.

| Probe | Pregunta | Si falla |
|---|---|---|
| **readiness** | ¿Puede atender tráfico **ahora**? | Se le quita del Service. Sigue vivo |
| **liveness** | ¿Está colgado sin remedio? | **Se mata y reinicia el pod** |
| **startup** | ¿Terminó de arrancar? | Suspende las otras dos mientras tanto |

```yaml
readinessProbe:
  httpGet: { path: /healthz/, port: 8000 }
  initialDelaySeconds: 5
  periodSeconds: 10
livenessProbe:
  httpGet: { path: /healthz/, port: 8000 }
  initialDelaySeconds: 30
  periodSeconds: 20
  failureThreshold: 3
```

**Trampas:**

- **Una `liveness` que consulta la base de datos causa un apagón masivo.** Si
  la BD cae, *todas* las réplicas fallan la probe y K8s las reinicia en bucle
  — cuando el problema no era de ellas. La `liveness` debe comprobar solo que
  **el proceso responde**; las dependencias van en la `readiness`.
- **`initialDelaySeconds` corto en la `liveness`** mata el pod antes de que
  termine de arrancar, y entra en `CrashLoopBackOff` eterno. Para arranques
  lentos, `startupProbe` en vez de inflar el delay.
- Endpoint de salud **barato**: si la probe cuesta cara, la ejecutas cada 10
  segundos por réplica para siempre.

---

## 3. `resources`: sin ellos, el clúster es una lotería

```yaml
resources:
  requests: { cpu: "100m", memory: "256Mi" }   # lo que el scheduler reserva
  limits:   { memory: "512Mi" }                # tope duro
```

- **`requests` es lo que el planificador usa para decidir dónde cabe el pod.**
  Sin `requests`, K8s asume ~0 y mete pods en nodos sin recursos reales: todo
  parece bien hasta que el nodo se satura y empieza a expulsar pods.
- **`limits` de memoria siempre**: superarlo mata el contenedor con `OOMKilled`
  — feo, pero acotado. Sin límite, un pod con fuga se lleva el nodo entero y
  con él a los vecinos.
- **`limits` de CPU: con cuidado.** La CPU se *estrangula* (throttling), no se
  mata: un límite bajo produce latencias altísimas difíciles de diagnosticar.
  Muchos equipos ponen `requests` de CPU y omiten el `limit` a propósito.
- Empezar midiendo, no adivinando. Un `limit` inventado se convierte en un
  incidente a las 3 AM.

---

## 4. Seguridad mínima del pod

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 10001
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities: { drop: ["ALL"] }
```

- **`runAsNonRoot` exige que la imagen ya traiga un usuario** — se prepara en
  el Dockerfile ([[docker]], regla 2). Si la imagen corre como root, el pod ni
  arranca.
- **`readOnlyRootFilesystem: true`** y montar un `emptyDir` para lo que
  necesite escribir (`/tmp`). Un atacante no puede dejar binarios.
- **Pod Security Admission** a nivel de namespace (reemplazó a las
  PodSecurityPolicy, eliminadas en 1.25):
  ```yaml
  metadata:
    labels:
      pod-security.kubernetes.io/enforce: restricted
  ```
- **NetworkPolicy por defecto deniega.** Sin ellas, cualquier pod del clúster
  habla con cualquier otro: un contenedor comprometido llega directo a la base
  de datos.
- **ServiceAccount dedicado con RBAC mínimo**, nunca la `default` del
  namespace, y `automountServiceAccountToken: false` si la app no llama a la
  API de K8s.

---

## 5. Configuración y secretos

- **ConfigMap** para configuración no sensible; **Secret** para lo demás. Se
  inyectan como variables de entorno o se montan como archivos — nunca
  horneados en la imagen ([[docker]]) ni en el manifiesto.
- **Un `Secret` de K8s NO está cifrado: es base64, que es codificación, no
  cifrado.** Cualquiera con permiso de lectura sobre el namespace lo ve en
  claro. Por eso:
  - **jamás commitear un `Secret` con datos reales** al repo;
  - usar **External Secrets Operator** (lee del gestor del proveedor) o
    **Sealed Secrets** (cifrado asimétrico, seguro de versionar);
  - habilitar *encryption at rest* en etcd del lado del clúster.
- **Un cambio de ConfigMap no reinicia los pods.** El valor viejo sigue en
  memoria y el despliegue "no hace nada". Kustomize resuelve esto con
  `configMapGenerator`, que añade un hash al nombre y fuerza el rollout.

---

## 6. Despliegue sin caídas

```yaml
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate: { maxSurge: 1, maxUnavailable: 0 }
```

- **`maxUnavailable: 0`** para que nunca baje la capacidad durante el
  despliegue (a costa de un pod extra temporal).
- **`PodDisruptionBudget`** para que un drenaje de nodo no se lleve todas las
  réplicas a la vez:
  ```yaml
  spec: { minAvailable: 2, selector: { matchLabels: { app: miapp } } }
  ```
- **Apagado elegante**: la app debe atender `SIGTERM` cerrando conexiones
  abiertas. `terminationGracePeriodSeconds` acorde, y un `preStop` con unos
  segundos de espera para que el balanceador deje de mandar tráfico antes de
  que el proceso muera (si no, se pierden peticiones en cada despliegue).
- **Migraciones de BD no van en el `CMD` del contenedor** cuando hay varias
  réplicas: tres pods corriendo `migrate` a la vez chocan. Van en un `Job`
  (o `initContainer` con bloqueo) previo al rollout.
- `kubectl rollout status` en CI para que el pipeline **falle si el despliegue
  no converge**, y `kubectl rollout undo` como plan de vuelta atrás.

---

## 7. Depuración: leer antes de reiniciar

Orden que resuelve la mayoría de los casos:

```bash
kubectl get pods                     # ¿en qué estado está?
kubectl describe pod <pod>           # Events al final: la causa suele estar ahí
kubectl logs <pod> --previous        # logs del contenedor que MURIÓ (clave en CrashLoop)
kubectl get events --sort-by=.lastTimestamp
```

| Estado | Causa habitual |
|---|---|
| `ImagePullBackOff` | Tag inexistente o falta credencial del registry |
| `CrashLoopBackOff` | La app muere al arrancar — leer `logs --previous` |
| `Pending` | Ningún nodo satisface los `requests`, o falta un volumen |
| `OOMKilled` | Superó el `limit` de memoria |
| `Running` pero sin tráfico | La `readiness` falla, o el selector del Service no coincide |

**No reiniciar a ciegas.** Un `delete pod` "arregla" el síntoma y borra la
evidencia; el fallo vuelve en el próximo despliegue. Diagnosticar contra el
estado real antes de tocar nada — la misma disciplina que aplica a depurar
servicios en local.

---

## Checklist antes de desplegar un servicio

- [ ] Imagen con tag inmutable (nunca `latest`), construida por CI.
- [ ] `readiness` y `liveness` distintas; la `liveness` no toca dependencias.
- [ ] `requests` en todos los contenedores; `limits` de memoria siempre.
- [ ] `runAsNonRoot`, capabilities `drop: ALL`, filesystem de solo lectura.
- [ ] Cero secretos reales en el repo; ConfigMap/Secret montados, no horneados.
- [ ] `maxUnavailable: 0` y PodDisruptionBudget si importa la disponibilidad.
- [ ] Migraciones en un Job aparte, no en el arranque de cada réplica.
- [ ] Manejo de `SIGTERM` verificado (no se pierden peticiones al desplegar).
- [ ] `kubectl rollout status` en el pipeline; rollback probado al menos una vez.
- [ ] NetworkPolicy y ServiceAccount con permisos mínimos.

## Ver también

[[docker]] para la imagen que corre en estos pods · [[terraform]] para crear el
clúster y su red · [[github-actions]] / [[jenkins]] para el pipeline que
construye, publica y hace `rollout` · [[python-backend]] para el `/healthz/`
que consumen las probes · [[arquitectura-software]] para decidir qué servicios
existen antes de orquestarlos.

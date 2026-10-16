---
name: terraform
description: >
  Estándares de infraestructura como código de Nicolás Cano Leal con Terraform:
  estado remoto con bloqueo, versiones fijadas, módulos con contrato claro,
  secretos fuera del estado, y plan revisado antes de todo apply. USAR SIEMPRE
  que se escriba o revise HCL (`.tf`), se diseñe la estructura de un repo de
  infraestructura, se configure un backend de estado, o se automatice
  `plan`/`apply` en CI — aunque no se pida "sigue mis estándares".
---

# Terraform — estándares de Nicolás Cano Leal

> Terraform describe **infraestructura**: lo que existe antes de que el
> contenedor arranque (red, base de datos, clúster, DNS, IAM). No compite con
> [[docker]] ni con [[kubernetes]]: los precede. La regla que ordena todo es
> **el estado es el activo crítico** — perderlo o corromperlo cuesta más que
> cualquier bug de HCL.

## Stack por defecto

Terraform 1.9+ (o **OpenTofu** si el proyecto quiere licencia MPL) · backend
**S3 con bloqueo nativo** (o el equivalente del proveedor) · `tflint` +
`terraform validate` + `terraform fmt -check` en CI · `tfsec`/`checkov` para
seguridad · un *workspace* o directorio por entorno.

---

## 1. El estado: remoto, bloqueado y cifrado — desde el primer commit

Un `terraform.tfstate` local es un fallo esperando ocurrir: no se puede
compartir, no se puede bloquear, y **contiene secretos en claro**.

```hcl
terraform {
  required_version = "~> 1.9"

  backend "s3" {
    bucket       = "miorg-tfstate"
    key          = "prod/red/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true   # bloqueo nativo de S3
  }
}
```

- **`use_lockfile = true` es la forma vigente de bloquear.** El bloqueo por
  tabla DynamoDB (`dynamodb_table`) está **deprecado** y se eliminará en una
  versión futura; solo se mantiene junto al nuevo para migrar desde versiones
  antiguas. En proyectos nuevos, no usar DynamoDB.
- **Sin bloqueo, dos `apply` concurrentes corrompen el estado.** No es
  hipotético: pasa la primera vez que dos personas trabajan el mismo día.
- **`encrypt = true` siempre**: el estado guarda contraseñas de RDS, claves y
  todo output marcado `sensitive`.
- **Versionado activado en el bucket**, para poder volver atrás un estado
  corrupto.
- **`key` distinto por entorno y por componente.** Un único estado gigante
  hace que un cambio en DNS bloquee un despliegue de base de datos.
- **Nunca commitear `.tfstate`, `.tfstate.backup` ni `.terraform/`.**
  `.gitignore` desde el commit inicial.

---

## 2. Versiones fijadas — o el `apply` de mañana no es el de hoy

```hcl
terraform {
  required_version = "~> 1.9"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.70"   # pesimista: permite 5.x, bloquea el salto a 6.0
    }
  }
}
```

- **`~>` (pessimistic constraint)**: acepta parches y menores, bloquea el
  mayor. Sin restricción, un proveedor publica una versión mayor y tu `apply`
  cambia de comportamiento sin que hayas tocado nada.
- **`.terraform.lock.hcl` SÍ se commitea.** Es el equivalente a un
  `package-lock.json`: garantiza el mismo proveedor en tu máquina y en CI.
- Actualizar proveedores es un **cambio deliberado con su propio `plan`
  revisado**, nunca un efecto colateral.

---

## 3. Estructura del repositorio

```
infra/
├── modules/
│   └── red/                 # módulo reutilizable, sin valores de entorno dentro
│       ├── main.tf
│       ├── variables.tf     # contrato de entrada
│       ├── outputs.tf       # contrato de salida
│       └── README.md        # qué crea y qué exige
└── envs/
    ├── dev/
    │   ├── main.tf          # invoca módulos con los valores de dev
    │   ├── backend.tf
    │   └── terraform.tfvars
    └── prod/
        └── ...
```

- **Un módulo no conoce el entorno.** Si adentro hay un `if var.entorno ==
  "prod"`, deja de ser reutilizable: eso se parametriza como variable.
- **`variables.tf` con `description` y `type` en todas.** Una variable sin
  tipo acepta cualquier cosa y falla en `apply`, no en `plan`.
- **`validation` para lo que se puede verificar temprano:**

```hcl
variable "entorno" {
  description = "Entorno de despliegue."
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.entorno)
    error_message = "entorno debe ser dev, staging o prod."
  }
}
```

- **Ningún `default` para lo que en producción debe ser explícito** (igual que
  `ALLOWED_HOSTS` sin default en [[python-backend]]): faltar la variable debe
  ser un fallo ruidoso, no un valor silencioso.

---

## 4. Secretos: nunca en HCL, y ojo con el estado

- **Cero secretos en `.tf` o `.tfvars` versionados.** Vienen de variables de
  entorno (`TF_VAR_*`), del gestor de secretos del proveedor (Secrets Manager,
  Vault) o del credential store del CI ([[jenkins]] / [[github-actions]]).
- **`sensitive = true`** en variables y outputs con secretos: evita que se
  impriman en el log del `plan`, que en CI es público para todo el equipo.
- **Advertencia clave: `sensitive` oculta la salida, NO cifra el estado.** El
  valor queda en claro dentro del `.tfstate`. De ahí que el backend deba estar
  cifrado y con acceso restringido — cualquiera que lea el bucket lee los
  secretos.
- **Recurso mejor que dato hardcodeado**: generar la contraseña con
  `random_password` y guardarla en el gestor de secretos, en vez de inventarla
  a mano y pegarla en una variable.

---

## 5. Reglas no negociables de operación

1. **`plan` revisado antes de todo `apply`.** El `plan` es el único momento en
   que ves *qué se va a destruir*. Leerlo entero, especialmente las líneas
   `-/+ destroy and then create replacement`.
2. **En CI: `plan` automático, `apply` con aprobación humana.** Un `apply`
   automático en `main` sobre producción es cómo se borra una base de datos un
   viernes. `plan` en cada PR (para revisarlo), `apply` tras aprobación.
3. **`terraform fmt -check` y `validate` en CI**, antes de cualquier plan
   — verificaciones rápidas primero (misma cascada que [[github-actions]]).
4. **Nunca editar recursos a mano en la consola web.** Produce *drift*: el
   estado deja de reflejar la realidad y el próximo `apply` deshace el cambio
   manual sin avisar. Si hubo que tocar algo urgente, reflejarlo en HCL
   inmediatamente después.
5. **`prevent_destroy` en lo irreemplazable** (bases de datos, buckets con
   datos):
   ```hcl
   lifecycle { prevent_destroy = true }
   ```
6. **Etiquetar todo** (`tags`) con proyecto, entorno y "gestionado por
   Terraform" — para que nadie borre a mano algo que el estado necesita.

---

## 6. Trampas conocidas

- **`terraform destroy` no pregunta dos veces por entorno.** Correrlo en el
  directorio equivocado destruye producción. Trabajar siempre desde
  `envs/<entorno>/` y confirmar el `plan` antes.
- **Renombrar un recurso en HCL = destruir y recrear.** Terraform identifica
  por la dirección (`aws_instance.web`), no por el nombre del recurso en la
  nube. Para renombrar sin recrear, usar el bloque `moved`:
  ```hcl
  moved {
    from = aws_instance.web
    to   = aws_instance.servidor_web
  }
  ```
- **`count` vs `for_each`**: con `count`, borrar un elemento del medio
  **reindexa** todos los siguientes y los recrea. `for_each` sobre un mapa o
  set los identifica por clave estable. Preferir `for_each` casi siempre.
- **Dependencias implícitas antes que `depends_on`.** Referenciar
  `aws_vpc.main.id` ya crea la dependencia; `depends_on` explícito es para
  las que Terraform no puede inferir, y usado de más ensucia el grafo.
- **El `plan` no garantiza el `apply`.** Entre uno y otro el mundo cambia
  (cuota agotada, recurso borrado a mano). Guardar el plan
  (`terraform plan -out=tfplan` y `apply tfplan`) reduce la ventana.
- **Módulos de terceros sin versión fijada** (`source` de Git sin `?ref=`) son
  una dependencia que cambia sola. Fijar tag siempre.

---

## Checklist antes de dar por terminado un módulo

- [ ] Backend remoto con `use_lockfile`, cifrado y versionado.
- [ ] `required_version` y versiones de proveedor con `~>`.
- [ ] `.terraform.lock.hcl` commiteado; `.tfstate` y `.terraform/` ignorados.
- [ ] Todas las variables con `type` y `description`; sin defaults peligrosos.
- [ ] Cero secretos en el repo; `sensitive = true` donde corresponde.
- [ ] `fmt -check`, `validate` y `tflint` limpios en CI.
- [ ] `plan` revisado línea por línea; nada que destruya sin querer.
- [ ] `prevent_destroy` en recursos con datos.
- [ ] README del módulo: qué crea, qué exige, qué devuelve.

## Ver también

[[kubernetes]] para lo que se despliega **sobre** la infraestructura que
Terraform crea · [[docker]] para las imágenes que corren ahí ·
[[github-actions]] / [[jenkins]] para automatizar `plan` y `apply` con
aprobación · [[arquitectura-software]] para decidir qué componentes existen
antes de escribirlos en HCL.

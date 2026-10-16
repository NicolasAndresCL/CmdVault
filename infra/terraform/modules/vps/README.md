# Módulo `vps`

VPS para CmdVault en AWS: una EC2 Ubuntu 24.04 con IP elástica y un security group mínimo. No instala
software (sin `user_data`): eso lo hace `infra/ansible`.

## Qué crea

| Recurso | Detalle |
|---|---|
| `aws_instance.vps` | Ubuntu 24.04 de Canonical (AMI más reciente), disco gp3 cifrado, **IMDSv2 obligatorio**; `ignore_changes = [ami]` para que una AMI nueva no recree el servidor |
| `aws_eip.vps` | IP pública fija |
| `aws_key_pair.admin` | Llave SSH del administrador |
| `aws_security_group.vps` + reglas | Entrada: SSH solo desde `cidr_admin_ssh`, HTTP/HTTPS públicos. Salida: TCP 80/443 (excepción Trivy AWS-0104 justificada en `main.tf`) |

## Qué exige

| Variable | Tipo | Default | Validación |
|---|---|---|---|
| `nombre` | string | — | 3–40 caracteres `[a-z0-9-]` |
| `llave_publica_ssh` | string | — | empieza con `ssh-ed25519 ` o `ssh-rsa ` |
| `cidr_admin_ssh` | list(string) | — (**obligatoria**) | CIDR válidos; **rechaza `0.0.0.0/0`** |
| `tipo_instancia` | string | `t3.small` | — |
| `disco_gb` | number | `20` | 10–200 |
| `tags` | map(string) | `{}` | — |

Terraform `~> 1.16`, proveedor `hashicorp/aws ~> 6.69`.

## Qué devuelve

`ip_publica`, `instancia_id`, `security_group_id`, `ssh` (comando listo) e `inventario_ansible` (bloque YAML
para `infra/ansible/inventory/hosts.yml`).

## Uso

```hcl
module "vps" {
  source            = "../../modules/vps"
  nombre            = "cmdvault-prod"
  llave_publica_ssh = var.llave_publica_ssh
  cidr_admin_ssh    = ["203.0.113.7/32"]
}
```

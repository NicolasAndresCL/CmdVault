variable "nombre" {
  description = "Prefijo de nombres y tag Name de los recursos (p. ej. cmdvault-prod)."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9-]{3,40}$", var.nombre))
    error_message = "nombre: 3 a 40 caracteres en minúscula, dígitos o guiones."
  }
}

variable "tipo_instancia" {
  description = "Tipo de instancia EC2. CmdVault (Postgres + API + UI) corre holgado en 2 GB de RAM."
  type        = string
  default     = "t3.small"
}

variable "disco_gb" {
  description = "Tamaño del disco raíz gp3 en GB."
  type        = number
  default     = 20

  validation {
    condition     = var.disco_gb >= 10 && var.disco_gb <= 200
    error_message = "disco_gb debe estar entre 10 y 200."
  }
}

variable "llave_publica_ssh" {
  description = "Contenido de la llave pública SSH (ed25519) del usuario administrador."
  type        = string

  validation {
    condition     = can(regex("^ssh-(ed25519|rsa) ", var.llave_publica_ssh))
    error_message = "llave_publica_ssh debe empezar con 'ssh-ed25519 ' o 'ssh-rsa '."
  }
}

variable "cidr_admin_ssh" {
  description = "Rangos CIDR autorizados a entrar por SSH (tu IP pública /32). Sin default: debe ser explícito."
  type        = list(string)

  validation {
    condition     = length(var.cidr_admin_ssh) > 0 && alltrue([for c in var.cidr_admin_ssh : can(cidrhost(c, 0))])
    error_message = "cidr_admin_ssh debe contener al menos un CIDR válido (p. ej. 203.0.113.7/32)."
  }

  validation {
    condition     = !contains(var.cidr_admin_ssh, "0.0.0.0/0")
    error_message = "No se permite SSH abierto a todo Internet (0.0.0.0/0)."
  }
}

variable "tags" {
  description = "Tags adicionales para todos los recursos."
  type        = map(string)
  default     = {}
}

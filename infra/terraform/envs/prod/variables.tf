variable "region" {
  description = "Región de AWS."
  type        = string
  default     = "us-east-1"
}

variable "tipo_instancia" {
  description = "Tipo de instancia EC2."
  type        = string
  default     = "t3.small"
}

variable "disco_gb" {
  description = "Disco raíz en GB."
  type        = number
  default     = 20
}

variable "llave_publica_ssh" {
  description = "Llave pública SSH del administrador (TF_VAR_llave_publica_ssh o terraform.tfvars)."
  type        = string
}

variable "cidr_admin_ssh" {
  description = "CIDR con acceso SSH: tu IP pública /32. Obligatorio, sin default."
  type        = list(string)
}

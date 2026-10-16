module "vps" {
  source = "../../modules/vps"

  nombre            = "cmdvault-prod"
  tipo_instancia    = var.tipo_instancia
  disco_gb          = var.disco_gb
  llave_publica_ssh = var.llave_publica_ssh
  cidr_admin_ssh    = var.cidr_admin_ssh
}

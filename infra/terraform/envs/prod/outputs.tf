output "ip_publica" {
  description = "IP elástica del VPS."
  value       = module.vps.ip_publica
}

output "ssh" {
  description = "Comando SSH."
  value       = module.vps.ssh
}

output "inventario_ansible" {
  description = "Pegar en infra/ansible/inventory/hosts.yml."
  value       = module.vps.inventario_ansible
}

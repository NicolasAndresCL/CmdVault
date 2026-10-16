output "ip_publica" {
  description = "IP elástica del VPS."
  value       = aws_eip.vps.public_ip
}

output "instancia_id" {
  description = "ID de la instancia EC2 (para aws ssm start-session o la consola)."
  value       = aws_instance.vps.id
}

output "security_group_id" {
  description = "ID del security group del VPS."
  value       = aws_security_group.vps.id
}

output "ssh" {
  description = "Comando para entrar por SSH."
  value       = "ssh ubuntu@${aws_eip.vps.public_ip}"
}

output "inventario_ansible" {
  description = "Bloque YAML listo para infra/ansible/inventory/hosts.yml."
  value       = <<-YAML
    cmdvault:
      hosts:
        ${var.nombre}:
          ansible_host: ${aws_eip.vps.public_ip}
          ansible_user: ubuntu
  YAML
}

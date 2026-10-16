# VPS para CmdVault: una instancia EC2 Ubuntu 24.04 con IP elástica, SSH restringido
# y solo 80/443 públicos. El software lo instala Ansible (infra/ansible), no user_data.

locals {
  tags = merge(var.tags, {
    Name     = var.nombre
    Proyecto = "cmdvault"
    Gestion  = "terraform"
    Modulo   = "vps"
  })
}

# Ubuntu 24.04 LTS oficial de Canonical (owner 099720109477), última imagen gp3.
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_key_pair" "admin" {
  key_name   = "${var.nombre}-admin"
  public_key = var.llave_publica_ssh
  tags       = local.tags
}

resource "aws_security_group" "vps" {
  name        = "${var.nombre}-sg"
  description = "CmdVault: SSH solo desde admin, HTTP/HTTPS publicos"
  tags        = local.tags
}

resource "aws_vpc_security_group_ingress_rule" "ssh" {
  for_each = toset(var.cidr_admin_ssh)

  security_group_id = aws_security_group.vps.id
  description       = "SSH administrador"
  ip_protocol       = "tcp"
  from_port         = 22
  to_port           = 22
  cidr_ipv4         = each.value
}

resource "aws_vpc_security_group_ingress_rule" "web" {
  for_each = { http = 80, https = 443 }

  security_group_id = aws_security_group.vps.id
  description       = upper(each.key)
  ip_protocol       = "tcp"
  from_port         = each.value
  to_port           = each.value
  cidr_ipv4         = "0.0.0.0/0"
}

# Salida solo HTTP/HTTPS: apt, Docker Hub y GitHub no tienen IPs fijas, así que el destino
# no se puede acotar. DNS y NTP de la VPC (169.254.169.253/.123) no pasan por el security group.
#trivy:ignore:AWS-0104
resource "aws_vpc_security_group_egress_rule" "web" {
  for_each = { http = 80, https = 443 }

  security_group_id = aws_security_group.vps.id
  description       = "Salida ${upper(each.key)} (paquetes e imagenes)"
  ip_protocol       = "tcp"
  from_port         = each.value
  to_port           = each.value
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_instance" "vps" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.tipo_instancia
  key_name               = aws_key_pair.admin.key_name
  vpc_security_group_ids = [aws_security_group.vps.id]

  # IMDSv2 obligatorio: bloquea el robo de credenciales por SSRF contra 169.254.169.254.
  metadata_options {
    http_tokens   = "required"
    http_endpoint = "enabled"
  }

  root_block_device {
    volume_type           = "gp3"
    volume_size           = var.disco_gb
    encrypted             = true
    delete_on_termination = true
  }

  tags        = local.tags
  volume_tags = local.tags

  lifecycle {
    # Una AMI nueva no debe recrear el servidor en cada plan: se cambia a propósito.
    ignore_changes = [ami]
  }
}

resource "aws_eip" "vps" {
  domain   = "vpc"
  instance = aws_instance.vps.id
  tags     = local.tags
}

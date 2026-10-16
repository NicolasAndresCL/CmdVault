terraform {
  required_version = "~> 1.16"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.69"
    }
  }

  # Estado remoto cifrado con bloqueo nativo de S3 (sin DynamoDB, deprecado).
  # Configuración parcial: bucket/key/región van en backend.hcl (no versionado).
  #   terraform init -backend-config=backend.hcl
  backend "s3" {
    encrypt      = true
    use_lockfile = true
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Proyecto = "cmdvault"
      Entorno  = "prod"
      Gestion  = "terraform"
    }
  }
}

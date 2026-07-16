terraform {
  required_version = ">= 1.5.0"
}

variable "environment" {
  type        = string
  description = "dev | staging | production"
}

variable "region" {
  type    = string
  default = "eu-central-1"
}

output "environment" {
  value = var.environment
}

# Stub modules — implement when cloud target is chosen
# module "vpc" { source = "./modules/vpc" }
# module "rds" { source = "./modules/rds" }
# module "elasticache" { source = "./modules/elasticache" }
# module "s3" { source = "./modules/s3" }

# Provider requirements for the Verra AWS infra (ADR-0014).
terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region  = var.region
  profile = var.aws_profile

  default_tags {
    tags = {
      Project     = "verra"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

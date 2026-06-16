# Verra cloud infra (skeleton, ADR-0014). Validate in a spike before adoption.
terraform { required_version = ">= 1.6" }
variable "region"      { type = string  default = "us-east-1" }
variable "environment" { type = string  default = "staging" }

# TODO modules: network (VPC, subnets), kubernetes (EKS/GKE), database (Postgres+pgvector),
# cache (Redis), object_store (S3), secrets (vault/KMS), observability (OTel), dns/cdn/waf.
# module "kubernetes" { source = "./modules/kubernetes" environment = var.environment }

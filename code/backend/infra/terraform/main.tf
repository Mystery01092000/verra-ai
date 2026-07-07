# Verra cloud infra (ADR-0014). Provider/versions: versions.tf · inputs: variables.tf
# Dev EC2 box: dev-ec2.tf

# TODO modules: network (VPC, subnets), kubernetes (EKS/GKE), database (Postgres+pgvector),
# cache (Redis), object_store (S3), secrets (vault/KMS), observability (OTel), dns/cdn/waf.
# module "kubernetes" { source = "./modules/kubernetes" environment = var.environment }

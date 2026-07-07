# infra/terraform

IaC for Verra's AWS footprint (ADR-0014). Multi-region for residency/DR planned;
fill modules per System Design §6/§9.

## Current scope

- `dev-ec2.tf` — the dev EC2 box (t3.micro, Amazon Linux 2023, us-east-1a),
  its `verra-key` key pair, and `verra-ec2-sg` security group. SSH/HTTP are
  restricted to the operator IP (`admin_cidr` variable — override when your IP changes:
  `terraform plan -var admin_cidr=NEW.IP.0.0/32`).

## Usage

```sh
terraform init
terraform plan -var environment=staging
```

State is local (`terraform.tfstate`, gitignored). The dev instance, key pair, and
security group were created imperatively on 2026-07-07 and imported:

```sh
terraform import aws_key_pair.verra verra-key
terraform import aws_security_group.dev_ec2 sg-0c6f575391ccc9094
terraform import aws_instance.dev i-07b5c858b27d10366
```

The private key for `verra-key` lives only at `~/.ssh/verra-key.pem` on the
operator machine — it is not in state or in this repo (only the public key is).

## TODO modules

network (VPC, subnets) · kubernetes (EKS/GKE) · database (Postgres+pgvector) ·
cache (Redis) · object_store (S3) · secrets (vault/KMS) · observability (OTel) ·
dns/cdn/waf — see `main.tf`.

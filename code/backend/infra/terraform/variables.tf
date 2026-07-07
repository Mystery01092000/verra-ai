variable "region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment tag"
  type        = string
  default     = "staging"
}

variable "aws_profile" {
  description = "Local AWS CLI profile used for authentication"
  type        = string
  default     = "verra"
}

variable "dev_instance_type" {
  description = "Instance type for the dev EC2 box (free-tier friendly)"
  type        = string
  default     = "t3.micro"
}

variable "dev_ami_id" {
  description = "Pinned AMI for the dev EC2 box (Amazon Linux 2023, x86_64, us-east-1). Pinned to avoid replacement drift from 'most recent' lookups."
  type        = string
  default     = "ami-0de568ccf3b0080d9"
}

variable "dev_ssh_public_key" {
  description = "Public key for the verra-key key pair (private key stays on the operator machine)"
  type        = string
  default     = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIORi5FqEked4zxmWVQItmbuuuodV5ny7aCqNTkdClm3P"
}

variable "admin_cidr" {
  description = "CIDR allowed to reach the dev instance over SSH/HTTP. Operator IP rotates (carrier NAT) — override per session: -var admin_cidr=$(dig +short txt ch whoami.cloudflare @1.1.1.1 | tr -d '\"')/32"
  type        = string
  default     = "223.190.80.243/32"

  validation {
    condition     = can(cidrnetmask(var.admin_cidr))
    error_message = "admin_cidr must be a valid CIDR block, e.g. 203.0.113.10/32."
  }
}

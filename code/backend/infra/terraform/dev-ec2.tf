# Dev EC2 box (launched 2026-07-07, imported into state — see README).
# Hosts nothing stateful; safe to stop/terminate. Public IP changes on stop/start.

resource "aws_key_pair" "verra" {
  key_name   = "verra-key"
  public_key = var.dev_ssh_public_key
}

resource "aws_security_group" "dev_ec2" {
  name        = "verra-ec2-sg"
  description = "SSH access for verra dev instance"

  tags = {
    Name = "verra-ec2-sg"
  }
}

resource "aws_vpc_security_group_ingress_rule" "dev_ssh" {
  security_group_id = aws_security_group.dev_ec2.id
  description       = "SSH from operator IP"
  cidr_ipv4         = var.admin_cidr
  from_port         = 22
  to_port           = 22
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "dev_http" {
  security_group_id = aws_security_group.dev_ec2.id
  description       = "HTTP from operator IP (dev smoke checks only)"
  cidr_ipv4         = var.admin_cidr
  from_port         = 80
  to_port           = 80
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "dev_all_out" {
  security_group_id = aws_security_group.dev_ec2.id
  description       = "Allow all outbound"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

resource "aws_instance" "dev" {
  ami                    = var.dev_ami_id
  instance_type          = var.dev_instance_type
  key_name               = aws_key_pair.verra.key_name
  vpc_security_group_ids = [aws_security_group.dev_ec2.id]

  root_block_device {
    volume_size = 8
    volume_type = "gp3"
  }

  tags = {
    Name = "verra"
  }

  lifecycle {
    # Instance was created before Terraform adoption; AMI updates require
    # a deliberate replacement, not a silent one on plan.
    ignore_changes = [ami]
  }
}

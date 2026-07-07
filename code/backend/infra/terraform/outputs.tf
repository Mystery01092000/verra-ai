output "dev_instance_id" {
  description = "ID of the dev EC2 instance"
  value       = aws_instance.dev.id
}

output "dev_public_ip" {
  description = "Current public IP of the dev EC2 instance (changes on stop/start)"
  value       = aws_instance.dev.public_ip
}

output "dev_ssh_command" {
  description = "SSH command for the dev EC2 instance"
  value       = "ssh -i ~/.ssh/verra-key.pem ec2-user@${aws_instance.dev.public_ip}"
}

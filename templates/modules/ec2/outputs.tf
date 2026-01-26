# templates/modules/ec2/outputs.tf

output "instance_ids" {
  description = "IDs delle istanze create"
  value       = aws_instance.web[*].id
}

output "public_ips" {
  description = "Lista degli IP pubblici assegnati alle istanze"
  value       = aws_instance.web[*].public_ip
}
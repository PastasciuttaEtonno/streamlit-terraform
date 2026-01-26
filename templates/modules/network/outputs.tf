output "vpc_id" {
  value = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "LISTA degli ID delle subnet pubbliche"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "LISTA degli ID delle subnet private"
  value       = aws_subnet.private[*].id
}
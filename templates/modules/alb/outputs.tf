output "dns_name" {
  description = "DNS pubblico del Load Balancer"
  value       = aws_lb.main.dns_name
}

output "security_group_id" {
  value = aws_security_group.alb_sg.id
}
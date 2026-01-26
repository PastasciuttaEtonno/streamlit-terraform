# outputs.tf root

output "vpc_id" {
  description = "L'ID dell VPC creata"
  value       = module.network.vpc_id
}

output "public_subnet_ids" {
  description = "Lista degli ID delle subnet pubbliche create"
  value       = module.network.public_subnet_ids
}

output "private_subnet_ids" {
  description = "Lista degli ID delle subnet private create"
  value       = module.network.private_subnet_ids
}

output "ec2_instance_ids" {
  description = "ID delle istanze EC2 create"
  value       = module.ec2.instance_ids
}

output "ec2_public_ips" {
  description = "IP Pubblici delle istanze create"
  value       = module.ec2.public_ips
}

output "alb_dns_name" {
  description = "URL del Load Balancer"
  # "try" evita errori se il modulo alb non esiste
  value       = try(module.alb.dns_name, "ALB non abilitato")
}

output "rds_endpoint" {
  value = try(module.rds.db_endpoint, "RDS non abilitato")
}
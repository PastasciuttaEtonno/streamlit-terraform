variable "environment_name" { type = string }
variable "vpc_id" { type = string }
variable "private_subnet_ids" { type = list(string) }
variable "ec2_security_group_id" { 
  type = string 
  description = "ID del SG delle EC2 per permettere l'accesso"
}

# Config DB
variable "identifier" { type = string }
variable "engine" { type = string }
variable "instance_class" { type = string }
variable "allocated_storage" { type = number }
variable "db_name" { type = string }
variable "username" { type = string }
variable "password" { type = string }
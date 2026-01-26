# DEFINIZIONE VARIABILI che verranno passate ai moduli

variable "environment_name" {
  description = "Nome dell'ambiente prefisso per le risorse"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR range per la VPC"
  type        = string
}

variable "public_subnet_cidr" {
  description = "CIDR per la subnet pubblica"
  type        = string
}

variable "private_subnet_cidr" {
  description = "CIDR per la subnet privata"
  type        = string
}

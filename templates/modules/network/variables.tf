variable "environment_name" { type = string }
variable "vpc_cidr"         { type = string }

variable "az_count" {
  description = "Numero di AZ da usare"
  type        = number
}

variable "public_subnet_count" {
  description = "Numero di subnet pubbliche da creare"
  type        = number
}

variable "private_subnet_count" {
  description = "Numero di subnet private da creare"
  type        = number
}
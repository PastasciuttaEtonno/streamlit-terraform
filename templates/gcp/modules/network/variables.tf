variable "project_id" {}
variable "region" {}
variable "network_name" {}
variable "subnet_cidr" {}
variable "enable_nat" {
  type    = bool
  default = false
}

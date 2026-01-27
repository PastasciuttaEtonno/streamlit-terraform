variable "project_id" {}
variable "region" {}
variable "zone" {}
variable "instance_name" {}
variable "machine_type" {}
variable "image_family" {}
variable "image_project" {}
variable "instance_count" {}
variable "network_name" {}
variable "subnetwork_name" {}
variable "subnet_type" {
  description = "public or private"
}

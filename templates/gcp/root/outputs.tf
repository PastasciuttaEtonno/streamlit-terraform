output "vpc_self_link" {
  description = "The URI of the VPC being created"
  value       = module.network.network_self_link
}

output "instance_ips" {
  description = "The internal and external IPs of the instances"
  value       = module.compute.instance_ips
}

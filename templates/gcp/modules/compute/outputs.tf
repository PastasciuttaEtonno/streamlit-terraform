output "instance_ips" {
  value = [
    for instance in google_compute_instance.vm : {
      name        = instance.name
      internal_ip = instance.network_interface.0.network_ip
      external_ip = length(instance.network_interface.0.access_config) > 0 ? instance.network_interface.0.access_config.0.nat_ip : "None"
    }
  ]
}

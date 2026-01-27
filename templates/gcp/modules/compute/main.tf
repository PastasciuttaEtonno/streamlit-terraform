resource "google_compute_instance" "vm" {
  count        = var.instance_count
  name         = "${var.instance_name}-${count.index}"
  machine_type = var.machine_type
  zone         = var.zone
  project      = var.project_id

  tags = var.subnet_type == "public" ? ["allow-public"] : []

  boot_disk {
    initialize_params {
      image = "${var.image_project}/${var.image_family}"
    }
  }

  network_interface {
    network    = var.network_name
    subnetwork = var.subnetwork_name

    # Access Config is what gives a public IP.
    # Dynamic block to conditionally create it.
    dynamic "access_config" {
      for_each = var.subnet_type == "public" ? [1] : []
      content {
        # Ephemeral IP
      }
    }
  }

  metadata_startup_script = "echo 'Hello from Terraform GCP' > /index.html"
}

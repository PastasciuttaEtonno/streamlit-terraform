# Variabili per il modulo ALB

variable "environment_name" { type = string }

variable "vpc_id" { type = string }

variable "public_subnet_ids" { type = list(string) }

variable "target_instance_ids" { type = list(string) }

variable "ingress_port" { type = number }

variable "listener_action_type" {
  description = "Tipo di azione: forward, redirect, o fixed-response"
  type        = string
  default     = "forward"
}

# Variabili Redirect
variable "redirect_protocol" { default = "HTTPS" }
variable "redirect_port" { default = "443" }
variable "redirect_status_code" { default = "HTTP_301" }

# Variabili Fixed Response
variable "fixed_response_body" { default = "Maintenance" }
variable "fixed_response_code" { default = "503" }
variable "fixed_response_content_type" { default = "text/plain" }
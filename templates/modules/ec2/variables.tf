variable "environment_name" {
  description = "Nome del progetto (usato per i Tag)"
  type        = string
}

variable "vpc_id" {
  description = "ID della VPC"
  type        = string
}

variable "subnet_id" {
  description = "ID della Subnet dove lanciare l'istanza"
  type        = string
}

variable "ami_id" {
  description = "AMI ID per l'istanza"
  type        = string
}

variable "instance_type" {
  description = "Tipo di istanza (es. t3.micro)"
  type        = string
}

variable "instance_count" {
  description = "Numero di istanze da creare"
  type        = number
  default     = 1
}

variable "associate_public_ip" {
  description = "Se true, associa un IP pubblico all'istanza. Se false, solo IP privato."
  type        = bool
  default     = true # Default a true per retro-compatibilità, ma lo sovrascriveremo
}

variable "allowed_ports" {
  description = "Lista di porte TCP da aprire"
  type        = list(number)
  default     = [22, 80]
}

variable "key_name" {
  description = "Nome della Key Pair AWS per l'accesso SSH"
  type        = string
  default     = null
}

variable "disk_size" {
  description = "Dimensione disco root in GB"
  type        = number
}

variable "disk_type" {
  description = "Tipo di volume EBS (gp3, io1...)"
  type        = string
}

variable "user_data_script" {
  description = "Script di avvio"
  type        = string
  default     = ""
}


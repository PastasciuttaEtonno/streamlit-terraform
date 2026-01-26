resource "aws_security_group" "web_sg" {
  name        = "${var.environment_name}-custom-sg"
  description = "Dynamic Security Group"
  vpc_id      = var.vpc_id

  # --- DYNAMIC BLOCK PER LE PORTE ---
  # Terraform cicla sulla lista 'var.allowed_ports'
  # e crea una regola 'ingress' per ogni porta.
  dynamic "ingress" {
    for_each = var.allowed_ports
    content {
      from_port   = ingress.value
      to_port     = ingress.value
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }

  # Egress standard (tutto aperto in uscita)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.environment_name}-SG" }
}

resource "aws_instance" "web" {
  count = var.instance_count

  ami           = var.ami_id
  instance_type = var.instance_type
  subnet_id     = var.subnet_id

  # Se la variabile è vuota, non assegna nessuna chiave
  key_name      = var.key_name != "" ? var.key_name : null
  
  associate_public_ip_address = var.associate_public_ip
  vpc_security_group_ids      = [aws_security_group.web_sg.id]

  # --- STORAGE CONFIG ---
  root_block_device {
    volume_size = var.disk_size
    volume_type = var.disk_type
    encrypted   = true # Best practice: sempre criptati
  }

  # --- USER DATA ---
  # Codifichiamo in base64 lo script passato da Python
  user_data_base64 = base64encode(var.user_data_script)
  # Rimpiazza l'istanza se lo script cambia (facoltativo, ma utile)
  user_data_replace_on_change = true

  tags = {
    Name = "${var.environment_name}-Server-${count.index + 1}"
  }
}
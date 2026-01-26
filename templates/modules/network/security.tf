# security.tf

resource "aws_security_group" "no_ingress" {
  name        = "${var.environment_name}-base-sg"
  description = "Security group with no ingress rule"
  vpc_id      = aws_vpc.main.id

  # NESSUN INGRESS (Entrata chiusa di default per sicurezza)
  # Le regole di ingresso specifiche verranno aggiunte nel modulo EC2 o separatamente

  # EGRESS (Uscita aperta a tutto - serve per scaricare pacchetti/update)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.environment_name} Base SG"
  }
}
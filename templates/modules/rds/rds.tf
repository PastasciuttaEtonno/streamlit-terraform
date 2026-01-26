# 1. Subnet Group (Raggruppa le subnet private)
resource "aws_db_subnet_group" "default" {
  name       = "${var.environment_name}-db-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name = "${var.environment_name} DB Subnet Group"
  }
}

# 2. Security Group del DB (CHAINING)
resource "aws_security_group" "rds_sg" {
  name        = "${var.environment_name}-rds-sg"
  description = "Allow access from EC2 only"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = var.engine == "mysql" ? 3306 : 5432
    to_port         = var.engine == "mysql" ? 3306 : 5432
    protocol        = "tcp"
    # QUI LA MAGIA: Non usiamo CIDR, ma un ID di Security Group
    security_groups = [var.ec2_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# 3. L'Istanza RDS
resource "aws_db_instance" "default" {
  identifier             = var.identifier
  allocated_storage      = var.allocated_storage
  db_name                = var.db_name
  engine                 = var.engine
  engine_version         = var.engine == "mysql" ? "8.0" : "16.3"
  instance_class         = var.instance_class
  username               = var.username
  password               = var.password
  parameter_group_name   = var.engine == "mysql" ? "default.mysql8.0" : "default.postgres16"
  skip_final_snapshot    = true # Importante per dev/test (distrugge veloce)
  publicly_accessible    = false # MAI esporre il DB a internet
  
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.default.name
}
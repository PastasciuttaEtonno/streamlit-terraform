# vpc.tf

# --- DATA SOURCES ---
# Recupera tutte le AZ disponibili nella regione (es. us-east-1a, 1b, 1c...)
data "aws_availability_zones" "available" {
  state = "available"
}

# --- VPC ---
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags = { Name = var.environment_name }
}

resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.main.id
  tags = { Name = var.environment_name }
}

# --- PUBLIC SUBNETS (Dinamiche) ---
resource "aws_subnet" "public" {
  # Crea N risorse in base al numero richiesto
  count = var.public_subnet_count

  vpc_id = aws_vpc.main.id
  
  # Calcola CIDR /24 progressivi: 10.0.0.0/24, 10.0.1.0/24, etc.
  cidr_block = cidrsubnet(var.vpc_cidr, 8, count.index)
  
  # Assegna AZ a rotazione: 1a, 1b, 1c, 1a...
  availability_zone = element(data.aws_availability_zones.available.names, count.index % var.az_count)
  
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.environment_name}-Public-${count.index + 1}"
  }
}

# --- PRIVATE SUBNETS (Dinamiche) ---
resource "aws_subnet" "private" {
  count = var.private_subnet_count

  vpc_id = aws_vpc.main.id
  
  # Offset di 100 per non sovrapporsi alle pubbliche: 10.0.100.0/24, etc.
  cidr_block = cidrsubnet(var.vpc_cidr, 8, count.index + 100)
  
  availability_zone = element(data.aws_availability_zones.available.names, count.index % var.az_count)

  tags = {
    Name = "${var.environment_name}-Private-${count.index + 1}"
  }
}

# --- ROUTING PUBBLICO ---
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gw.id
  }
  tags = { Name = "${var.environment_name}-Public-RT" }
}

resource "aws_route_table_association" "public" {
  count          = var.public_subnet_count
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}
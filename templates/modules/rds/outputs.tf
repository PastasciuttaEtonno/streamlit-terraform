output "db_endpoint" {
  description = "Indirizzo di connessione del DB"
  value       = aws_db_instance.default.address
}
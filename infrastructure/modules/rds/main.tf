# DB Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "${var.name_prefix}-${var.db_name}-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = merge(
    var.tags,
    {
      Name = "${var.name_prefix}-${var.db_name}-subnet-group"
    }
  )
}

# RDS PostgreSQL Instance - Simplified for fast startup
resource "aws_db_instance" "main" {
  identifier     = "${var.name_prefix}-${var.db_name}"
  engine         = "postgres"
  engine_version = "15"

  # Smallest instance class
  instance_class = "db.t3.micro"

  # Minimal storage configuration - Free tier eligible
  allocated_storage = 20
  storage_type      = "gp2"  # gp2 is free tier eligible (gp3 is not)
  storage_encrypted = false  # Faster startup without encryption

  # Database configuration
  db_name  = var.db_name
  username = var.master_username
  password = var.master_password
  port     = 5432

  # Network configuration
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [var.security_group_id]
  publicly_accessible    = true

  # No backups for faster startup
  backup_retention_period = 0
  skip_final_snapshot     = true

  # Single AZ for faster startup
  multi_az = false

  # No deletion protection
  deletion_protection = false

  # Apply changes immediately
  apply_immediately = true

  tags = merge(
    var.tags,
    {
      Name = "${var.name_prefix}-${var.db_name}"
    }
  )
}

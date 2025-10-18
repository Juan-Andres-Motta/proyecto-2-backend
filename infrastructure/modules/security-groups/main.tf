# ALB Security Group
resource "aws_security_group" "alb" {
  name        = "${var.name_prefix}-alb-sg"
  description = "Security group for Application Load Balancer"
  vpc_id      = var.vpc_id

  tags = merge(
    var.tags,
    {
      Name = "${var.name_prefix}-alb-sg"
    }
  )
}

# ALB Ingress - HTTP from internet
resource "aws_vpc_security_group_ingress_rule" "alb_http" {
  security_group_id = aws_security_group.alb.id
  description       = "HTTP from internet"

  cidr_ipv4   = "0.0.0.0/0"
  from_port   = 80
  to_port     = 80
  ip_protocol = "tcp"
}

# ALB Egress - to ECS tasks
resource "aws_vpc_security_group_egress_rule" "alb_to_ecs" {
  security_group_id = aws_security_group.alb.id
  description       = "Allow traffic to ECS tasks"

  referenced_security_group_id = aws_security_group.ecs_tasks.id
  from_port                    = 8000
  to_port                      = 8000
  ip_protocol                  = "tcp"
}

# ECS Tasks Security Group
resource "aws_security_group" "ecs_tasks" {
  name        = "${var.name_prefix}-ecs-tasks-sg"
  description = "Security group for ECS tasks"
  vpc_id      = var.vpc_id

  tags = merge(
    var.tags,
    {
      Name = "${var.name_prefix}-ecs-tasks-sg"
    }
  )
}

# ECS Ingress - from ALB
resource "aws_vpc_security_group_ingress_rule" "ecs_from_alb" {
  security_group_id = aws_security_group.ecs_tasks.id
  description       = "Allow traffic from ALB"

  referenced_security_group_id = aws_security_group.alb.id
  from_port                    = 8000
  to_port                      = 8000
  ip_protocol                  = "tcp"
}

# ECS Ingress - from other ECS tasks (Service Connect)
resource "aws_vpc_security_group_ingress_rule" "ecs_from_ecs" {
  security_group_id = aws_security_group.ecs_tasks.id
  description       = "Allow traffic from other ECS tasks (Service Connect)"

  referenced_security_group_id = aws_security_group.ecs_tasks.id
  from_port                    = 8000
  to_port                      = 8000
  ip_protocol                  = "tcp"
}

# ECS Egress - to internet (for ECR, package downloads)
resource "aws_vpc_security_group_egress_rule" "ecs_to_internet_https" {
  security_group_id = aws_security_group.ecs_tasks.id
  description       = "Allow HTTPS to internet for ECR and packages"

  cidr_ipv4   = "0.0.0.0/0"
  from_port   = 443
  to_port     = 443
  ip_protocol = "tcp"
}

# ECS Egress - to RDS
resource "aws_vpc_security_group_egress_rule" "ecs_to_rds" {
  security_group_id = aws_security_group.ecs_tasks.id
  description       = "Allow traffic to RDS"

  referenced_security_group_id = aws_security_group.rds.id
  from_port                    = 5432
  to_port                      = 5432
  ip_protocol                  = "tcp"
}

# ECS Egress - to other ECS tasks (Service Connect)
resource "aws_vpc_security_group_egress_rule" "ecs_to_ecs" {
  security_group_id = aws_security_group.ecs_tasks.id
  description       = "Allow traffic to other ECS tasks (Service Connect)"

  referenced_security_group_id = aws_security_group.ecs_tasks.id
  from_port                    = 8000
  to_port                      = 8000
  ip_protocol                  = "tcp"
}

# RDS Security Group
resource "aws_security_group" "rds" {
  name        = "${var.name_prefix}-rds-sg"
  description = "Security group for RDS databases"
  vpc_id      = var.vpc_id

  tags = merge(
    var.tags,
    {
      Name = "${var.name_prefix}-rds-sg"
    }
  )
}

# RDS Ingress - from ECS tasks only
resource "aws_vpc_security_group_ingress_rule" "rds_from_ecs" {
  security_group_id = aws_security_group.rds.id
  description       = "Allow PostgreSQL from ECS tasks"

  referenced_security_group_id = aws_security_group.ecs_tasks.id
  from_port                    = 5432
  to_port                      = 5432
  ip_protocol                  = "tcp"
}

# RDS Ingress - from any IP address (for external access)
resource "aws_vpc_security_group_ingress_rule" "rds_from_internet" {
  security_group_id = aws_security_group.rds.id
  description       = "Allow PostgreSQL from any IP address"

  cidr_ipv4   = "0.0.0.0/0"
  from_port   = 5432
  to_port     = 5432
  ip_protocol = "tcp"
}

locals {
  name_prefix = "medisupply-staging"
  common_tags = {
    ManagedBy   = "terraform"
    Environment = "staging"
  }
}

# Get latest Amazon Linux 2023 AMI
data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# VPC Module for staging
module "vpc" {
  source = "../modules/vpc"

  name_prefix = local.name_prefix
  tags        = local.common_tags
}

# Security Group for EC2
resource "aws_security_group" "ec2" {
  name_prefix = "${local.name_prefix}-ec2-"
  description = "Security group for staging EC2 instance"
  vpc_id      = module.vpc.vpc_id

  # SSH access
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allowed_ssh_cidr
    description = "SSH access"
  }

  # HTTP for BFF
  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "BFF HTTP"
  }

  # All microservices ports
  ingress {
    from_port   = 8001
    to_port     = 8006
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Microservices HTTP"
  }

  # Database ports (PostgreSQL)
  ingress {
    from_port   = 5432
    to_port     = 5437
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Database access (Postgres)"
  }

  # Outbound internet access
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound"
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-ec2-sg"
    }
  )
}

# IAM Role for EC2 (to pull from ECR)
resource "aws_iam_role" "ec2" {
  name = "${local.name_prefix}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# Attach ECR read policy
resource "aws_iam_role_policy_attachment" "ecr_read" {
  role       = aws_iam_role.ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

# Attach SSM policy for Systems Manager access
resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# IAM Instance Profile
resource "aws_iam_instance_profile" "ec2" {
  name = "${local.name_prefix}-ec2-profile"
  role = aws_iam_role.ec2.name

  tags = local.common_tags
}

# EC2 Instance
resource "aws_instance" "staging" {
  ami                    = data.aws_ami.amazon_linux_2023.id
  instance_type          = var.instance_type
  key_name               = var.key_name
  subnet_id              = module.vpc.public_subnet_ids[0]
  vpc_security_group_ids = [aws_security_group.ec2.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2.name

  root_block_device {
    volume_size           = var.volume_size
    volume_type           = "gp3"
    delete_on_termination = true
  }

  user_data = file("${path.module}/user-data.sh")

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-instance"
    }
  )
}

# Elastic IP for staging
resource "aws_eip" "staging" {
  instance = aws_instance.staging.id
  domain   = "vpc"

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-eip"
    }
  )
}

# ECS Configuration for staging
# Security Groups Module
module "security_groups" {
  source = "../modules/security-groups"

  name_prefix = local.name_prefix
  vpc_id      = module.vpc.vpc_id
  tags        = local.common_tags
}

# IAM Roles Module for ECS
module "iam" {
  source = "../modules/iam"

  name_prefix = local.name_prefix
  tags        = local.common_tags
}

# Remote state data source for common infrastructure
data "terraform_remote_state" "common" {
  backend = "local"

  config = {
    path = "../common/terraform.tfstate"
  }
}

# CloudWatch Log Groups (one per service)
module "cloudwatch" {
  source   = "../modules/cloudwatch"
  for_each = toset(["bff", "catalog", "client", "delivery", "inventory", "order", "seller"])

  name_prefix        = local.name_prefix
  service_name       = each.value
  log_retention_days = 1
  tags               = local.common_tags
}

# Application Load Balancer - DISABLED due to AWS account restriction
# TODO: Enable this after contacting AWS Support to lift load balancer restriction
# module "alb" {
#   source = "../modules/alb"
#
#   name_prefix           = local.name_prefix
#   vpc_id                = module.vpc.vpc_id
#   public_subnet_ids     = module.vpc.public_subnet_ids
#   alb_security_group_id = module.security_groups.alb_security_group_id
#   services              = ["bff", "catalog", "client", "delivery", "inventory", "order", "seller"]
#   service_container_ports = {
#     bff       = 8000
#     catalog   = 8000
#     client    = 8000
#     delivery  = 8000
#     inventory  = 8000
#     order     = 8000
#     seller    = 8000
#   }
#   tags = local.common_tags
# }

# ECS Cluster
module "ecs_cluster" {
  source = "../modules/ecs-cluster"

  cluster_name              = "${local.name_prefix}-cluster"
  service_connect_namespace = "medisupply-staging.local"
  tags                      = local.common_tags
}

# ECR Repositories (reuse production ECR)
data "aws_ecr_repository" "services" {
  for_each = toset(["bff", "catalog", "client", "delivery", "inventory", "order", "seller"])
  name     = each.value
}

# Shared RDS Database for all microservices
module "rds_shared" {
  source = "../modules/rds"

  name_prefix        = local.name_prefix
  db_name            = "medisupply"
  master_password    = var.db_password
  private_subnet_ids = module.vpc.public_subnet_ids
  security_group_id  = module.security_groups.rds_security_group_id
  tags               = local.common_tags
}

# ECS Task Definitions (one per service)
module "ecs_task_definition" {
  source   = "../modules/ecs-task-definition"
  for_each = toset(["bff", "catalog", "client", "delivery", "inventory", "order", "seller"])

  name_prefix = local.name_prefix
  service_name = each.value
  image_uri    = "${data.aws_ecr_repository.services[each.value].repository_url}:latest"
  cpu          = "256"
  memory       = "512"
  execution_role_arn    = module.iam.ecs_task_execution_role_arn
  task_role_arn         = module.iam.ecs_task_role_arn
  environment_variables = {
    bff = {
      CATALOG_URL   = "http://catalog.medisupply-staging.local:8000"
      CLIENT_URL    = "http://client.medisupply-staging.local:8000"
      DELIVERY_URL  = "http://delivery.medisupply-staging.local:8000"
      INVENTORY_URL = "http://inventory.medisupply-staging.local:8000"
      ORDER_URL     = "http://order.medisupply-staging.local:8000"
      SELLER_URL    = "http://seller.medisupply-staging.local:8000"
      SQS_REPORTS_QUEUE_URL = data.terraform_remote_state.common.outputs.sqs_reports_queue_url
      AWS_REGION            = var.aws_region
    }
    catalog   = { DATABASE_URL = "postgresql://postgres:${var.db_password}@${module.rds_shared.db_instance_address}:5432/medisupply" }
    client    = { DATABASE_URL = "postgresql://postgres:${var.db_password}@${module.rds_shared.db_instance_address}:5432/medisupply" }
    delivery  = { DATABASE_URL = "postgresql://postgres:${var.db_password}@${module.rds_shared.db_instance_address}:5432/medisupply" }
    inventory = {
      DATABASE_URL          = "postgresql://postgres:${var.db_password}@${module.rds_shared.db_instance_address}:5432/medisupply"
      S3_REPORTS_BUCKET     = data.terraform_remote_state.common.outputs.s3_inventory_reports_bucket_name
      SQS_REPORTS_QUEUE_URL = data.terraform_remote_state.common.outputs.sqs_reports_queue_url
      AWS_REGION            = var.aws_region
    }
    order = {
      DATABASE_URL          = "postgresql://postgres:${var.db_password}@${module.rds_shared.db_instance_address}:5432/medisupply"
      S3_REPORTS_BUCKET     = data.terraform_remote_state.common.outputs.s3_order_reports_bucket_name
      SQS_REPORTS_QUEUE_URL = data.terraform_remote_state.common.outputs.sqs_reports_queue_url
      AWS_REGION            = var.aws_region
    }
    seller = { DATABASE_URL = "postgresql://postgres:${var.db_password}@${module.rds_shared.db_instance_address}:5432/medisupply" }
  }[each.value]
  secrets = {}
  log_group_name    = module.cloudwatch[each.value].log_group_name
  aws_region        = var.aws_region
  container_port    = 8000
  health_check_path = "/${each.value}/health"
  tags              = local.common_tags
}

# ECS Services (one per service) - Running without ALB (using public IPs directly)
module "ecs_service" {
  source   = "../modules/ecs-service"
  for_each = toset(["bff", "catalog", "client", "delivery", "inventory", "order", "seller"])

  name_prefix                    = local.name_prefix
  service_name                   = each.value
  cluster_id                     = module.ecs_cluster.cluster_id
  task_definition_arn            = module.ecs_task_definition[each.value].task_definition_arn
  desired_count                  = 1
  subnet_ids                     = module.vpc.public_subnet_ids
  security_group_id              = module.security_groups.ecs_tasks_security_group_id
  # target_group_arn removed - no ALB available
  container_port                 = 8000
  service_connect_namespace_arn  = module.ecs_cluster.service_connect_namespace_arn
  service_connect_namespace_name = module.ecs_cluster.service_connect_namespace_name
  tags                           = local.common_tags
}

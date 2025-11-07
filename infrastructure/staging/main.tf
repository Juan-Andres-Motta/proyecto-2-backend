locals {
  name_prefix = "medisupply-staging"
  common_tags = {
    ManagedBy   = "terraform"
    Environment = "staging"
  }
}

# Retrieve DB password from AWS Secrets Manager
data "aws_secretsmanager_secret" "db_password" {
  name = "medisupply-db-password"
}

data "aws_secretsmanager_secret_version" "db_password" {
  secret_id = data.aws_secretsmanager_secret.db_password.id
}

# VPC Module for staging
module "vpc" {
  source = "../modules/vpc"

  name_prefix = local.name_prefix
  tags        = local.common_tags
}

# Security Groups Module (needed for RDS)
module "security_groups" {
  source = "../modules/security-groups"

  name_prefix = local.name_prefix
  vpc_id      = module.vpc.vpc_id
  tags        = local.common_tags
}

# IAM Roles Module (kept for IAM accounts)
module "iam" {
  source = "../modules/iam"

  name_prefix = local.name_prefix
  tags        = local.common_tags
}

# Remote state data source for common infrastructure (S3 buckets and SQS)
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

# Shared RDS Database for all microservices
module "rds_shared" {
  source = "../modules/rds"

  name_prefix        = local.name_prefix
  db_name            = "medisupply"
  master_password    = data.aws_secretsmanager_secret_version.db_password.secret_string
  private_subnet_ids = module.vpc.public_subnet_ids
  security_group_id  = module.security_groups.rds_security_group_id
  tags               = local.common_tags
}

# ============================================================================
# COMPUTE RESOURCES REMOVED
# ============================================================================
# The following resources have been removed from staging:
# - EC2 instance (aws_instance.staging)
# - Elastic IP (aws_eip.staging)
# - EC2 Security Group (aws_security_group.ec2)
# - EC2 IAM Role, Policy Attachments, Instance Profile
# - ECS Cluster (module.ecs_cluster)
# - ECS Task Definitions (module.ecs_task_definition)
# - ECS Services (module.ecs_service)
# - Application Load Balancer (already commented out)
#
# Retained resources:
# - VPC
# - IAM roles (for IAM accounts)
# - CloudWatch Log Groups (for logging)
# - Security Groups (for RDS)
# - RDS Shared Database (needed for staging database)
# - Access to shared S3 buckets via common infrastructure:
#   - medisupply-order-reports
#   - medisupply-inventory-reports
#   - medisupply-evidence
# - Access to shared SQS queue via common infrastructure:
#   - medisupply-reports-queue
# - Access to shared Cognito via common infrastructure
# ============================================================================

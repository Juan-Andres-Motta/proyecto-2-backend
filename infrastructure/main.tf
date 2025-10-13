locals {
  name_prefix = "medisupply"
  common_tags = {
    ManagedBy = "terraform"
  }

  # Service-specific environment variables
  service_env_vars = {
    bff = {
      CATALOG_URL   = "http://catalog.medisupply.local:8000"
      CLIENT_URL    = "http://client.medisupply.local:8000"
      DELIVERY_URL  = "http://delivery.medisupply.local:8000"
      INVENTORY_URL = "http://inventory.medisupply.local:8000"
      ORDER_URL     = "http://order.medisupply.local:8000"
      SELLER_URL    = "http://seller.medisupply.local:8000"
    }
    catalog = {
      DATABASE_URL = "postgresql://postgres:${var.db_master_password}@${module.rds_catalog.db_instance_address}:5432/catalogdb"
      LOG_LEVEL    = "INFO"
      DEBUG_SQL    = "false"
    }
    client = {
      DATABASE_URL = "postgresql://postgres:${var.db_master_password}@${module.rds_client.db_instance_address}:5432/client"
    }
    delivery = {
      DATABASE_URL = "postgresql://postgres:${var.db_master_password}@${module.rds_delivery.db_instance_address}:5432/delivery"
    }
    inventory = {
      DATABASE_URL = "postgresql://postgres:${var.db_master_password}@${module.rds_inventory.db_instance_address}:5432/inventory"
    }
    order = {
      DATABASE_URL = "postgresql://postgres:${var.db_master_password}@${module.rds_order.db_instance_address}:5432/orderdb"
    }
    seller = {
      DATABASE_URL = "postgresql://postgres:${var.db_master_password}@${module.rds_seller.db_instance_address}:5432/seller"
    }
  }
}

# VPC Module
module "vpc" {
  source = "./modules/vpc"

  name_prefix = local.name_prefix
  tags        = local.common_tags
}

# Security Groups Module
module "security_groups" {
  source = "./modules/security-groups"

  name_prefix = local.name_prefix
  vpc_id      = module.vpc.vpc_id
  tags        = local.common_tags
}

# IAM Roles Module
module "iam" {
  source = "./modules/iam"

  name_prefix = local.name_prefix
  tags        = local.common_tags
}

# CloudWatch Log Groups (one per service)
module "cloudwatch" {
  source   = "./modules/cloudwatch"
  for_each = toset(var.services)

  name_prefix         = local.name_prefix
  service_name        = each.value
  log_retention_days  = 1
  tags                = local.common_tags
}

# Application Load Balancer
module "alb" {
  source = "./modules/alb"

  name_prefix           = local.name_prefix
  vpc_id                = module.vpc.vpc_id
  public_subnet_ids     = module.vpc.public_subnet_ids
  alb_security_group_id = module.security_groups.alb_security_group_id
  services              = var.services
  tags                  = local.common_tags
}

# ECS Cluster
module "ecs_cluster" {
  source = "./modules/ecs-cluster"

  cluster_name              = "${local.name_prefix}-cluster"
  service_connect_namespace = "medisupply.local"
  tags                      = local.common_tags
}

# ECR Repositories
module "ecr" {
  source   = "./modules/ecr"
  for_each = toset(var.services)

  repository_name      = each.value
  image_tag_mutability = "MUTABLE"
  scan_on_push         = true
  common_tags          = local.common_tags
}

# ECS Task Definitions (one per service)
module "ecs_task_definition" {
  source   = "./modules/ecs-task-definition"
  for_each = toset(var.services)

  name_prefix          = local.name_prefix
  service_name         = each.value
  image_uri            = "${module.ecr[each.value].repository_url}:latest"
  cpu                  = "256"  # 0.25 vCPU
  memory               = "512"  # 0.5 GB
  execution_role_arn   = module.iam.ecs_task_execution_role_arn
  task_role_arn        = module.iam.ecs_task_role_arn
  environment_variables = local.service_env_vars[each.value]
  log_group_name       = module.cloudwatch[each.value].log_group_name
  aws_region           = var.aws_region
  container_port       = 8000
  tags                 = local.common_tags
}

# ECS Services (one per service)
module "ecs_service" {
  source   = "./modules/ecs-service"
  for_each = toset(var.services)

  name_prefix                    = local.name_prefix
  service_name                   = each.value
  cluster_id                     = module.ecs_cluster.cluster_id
  task_definition_arn            = module.ecs_task_definition[each.value].task_definition_arn
  desired_count                  = 1
  subnet_ids                     = module.vpc.public_subnet_ids
  security_group_id              = module.security_groups.ecs_tasks_security_group_id
  target_group_arn               = module.alb.target_group_arns[each.value]
  container_port                 = 8000
  service_connect_namespace_arn  = module.ecs_cluster.service_connect_namespace_arn
  service_connect_namespace_name = module.ecs_cluster.service_connect_namespace_name
  tags                           = local.common_tags

  depends_on = [module.alb]
}

# RDS Databases - One for each microservice
# Using cheapest possible configuration (db.t3.micro, 20GB storage)

module "rds_catalog" {
  source = "./modules/rds"

  name_prefix        = local.name_prefix
  db_name            = "catalogdb"
  master_password    = var.db_master_password
  private_subnet_ids = module.vpc.private_subnet_ids
  security_group_id  = module.security_groups.rds_security_group_id

  backup_retention_period = 1  # Minimal backups for cost savings
  tags                    = local.common_tags
}

module "rds_client" {
  source = "./modules/rds"

  name_prefix        = local.name_prefix
  db_name            = "client"
  master_password    = var.db_master_password
  private_subnet_ids = module.vpc.private_subnet_ids
  security_group_id  = module.security_groups.rds_security_group_id

  backup_retention_period = 1
  tags                    = local.common_tags
}

module "rds_delivery" {
  source = "./modules/rds"

  name_prefix        = local.name_prefix
  db_name            = "delivery"
  master_password    = var.db_master_password
  private_subnet_ids = module.vpc.private_subnet_ids
  security_group_id  = module.security_groups.rds_security_group_id

  backup_retention_period = 1
  tags                    = local.common_tags
}

module "rds_inventory" {
  source = "./modules/rds"

  name_prefix        = local.name_prefix
  db_name            = "inventory"
  master_password    = var.db_master_password
  private_subnet_ids = module.vpc.private_subnet_ids
  security_group_id  = module.security_groups.rds_security_group_id

  backup_retention_period = 1
  tags                    = local.common_tags
}

module "rds_order" {
  source = "./modules/rds"

  name_prefix        = local.name_prefix
  db_name            = "orderdb"
  master_password    = var.db_master_password
  private_subnet_ids = module.vpc.private_subnet_ids
  security_group_id  = module.security_groups.rds_security_group_id

  backup_retention_period = 1
  tags                    = local.common_tags
}

module "rds_seller" {
  source = "./modules/rds"

  name_prefix        = local.name_prefix
  db_name            = "seller"
  master_password    = var.db_master_password
  private_subnet_ids = module.vpc.private_subnet_ids
  security_group_id  = module.security_groups.rds_security_group_id

  backup_retention_period = 1
  tags                    = local.common_tags
}

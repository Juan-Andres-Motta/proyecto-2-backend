# Retrieve DB password from AWS Secrets Manager
data "aws_secretsmanager_secret" "db_password" {
  name = "medisupply-db-password"
}

data "aws_secretsmanager_secret_version" "db_password" {
  secret_id = data.aws_secretsmanager_secret.db_password.id
}

locals {
  name_prefix     = "medisupply"
  db_password     = data.aws_secretsmanager_secret_version.db_password.secret_string
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
      # Cognito Authentication Configuration
      AWS_COGNITO_USER_POOL_ID     = module.cognito.user_pool_id
      AWS_COGNITO_WEB_CLIENT_ID    = module.cognito.web_client_id
      AWS_COGNITO_MOBILE_CLIENT_ID = module.cognito.mobile_client_id
      AWS_COGNITO_REGION           = var.aws_region
      JWT_ISSUER_URL               = module.cognito.jwt_issuer_url
      JWT_JWKS_URL                 = module.cognito.jwks_url
    }
    catalog = {
      DATABASE_URL = "postgresql://postgres:${local.db_password}@${module.rds_catalog.db_instance_address}:5432/catalogdb2"
      LOG_LEVEL    = "INFO"
      DEBUG_SQL    = "false"
    }
    client = {
      DATABASE_URL = "postgresql://postgres:${local.db_password}@${module.rds_client.db_instance_address}:5432/client2"
    }
    delivery = {
      DATABASE_URL = "postgresql://postgres:${local.db_password}@${module.rds_delivery.db_instance_address}:5432/delivery2"
    }
    inventory = {
      DATABASE_URL          = "postgresql://postgres:${local.db_password}@${module.rds_inventory.db_instance_address}:5432/inventory2"
      S3_REPORTS_BUCKET     = data.terraform_remote_state.common.outputs.s3_inventory_reports_bucket_name
      SQS_REPORTS_QUEUE_URL = data.terraform_remote_state.common.outputs.sqs_reports_queue_url
      AWS_REGION            = var.aws_region
    }
    order = {
      DATABASE_URL          = "postgresql://postgres:${local.db_password}@${module.rds_order.db_instance_address}:5432/orderdb2"
      S3_REPORTS_BUCKET     = data.terraform_remote_state.common.outputs.s3_order_reports_bucket_name
      SQS_REPORTS_QUEUE_URL = data.terraform_remote_state.common.outputs.sqs_reports_queue_url
      AWS_REGION            = var.aws_region
    }
    seller = {
      DATABASE_URL = "postgresql://postgres:${local.db_password}@${module.rds_seller.db_instance_address}:5432/seller2"
    }
  }

  # Service-specific health check paths
  service_health_check_paths = {
    bff       = "/bff/health"
    catalog   = "/catalog/health"
    client    = "/client/health"
    delivery  = "/delivery/health"
    inventory = "/inventory/health"
    order     = "/order/health"
    seller    = "/seller/health"
  }

  # Service-specific container ports (all services run on port 8000)
  service_container_ports = {
    bff       = 8000
    catalog   = 8000
    client    = 8000
    delivery  = 8000
    inventory = 8000
    order     = 8000
    seller    = 8000
  }
}

# VPC Module
module "vpc" {
  source = "../modules/vpc"

  name_prefix = local.name_prefix
  tags        = local.common_tags
}

# Security Groups Module
module "security_groups" {
  source = "../modules/security-groups"

  name_prefix = local.name_prefix
  vpc_id      = module.vpc.vpc_id
  tags        = local.common_tags
}

# IAM Roles Module
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

# Cognito Module for Authentication
module "cognito" {
  source = "../modules/cognito"

  name_prefix = local.name_prefix
  tags        = local.common_tags

  # Frontend callback URLs (update with actual URLs when deployed)
  web_callback_urls    = ["http://localhost:3000/callback", "https://localhost:3000/callback"]
  web_logout_urls      = ["http://localhost:3000/", "https://localhost:3000/"]
  mobile_callback_urls = ["medisupply://callback"]
  mobile_logout_urls   = ["medisupply://logout"]
}

# CloudWatch Log Groups (one per service)
module "cloudwatch" {
  source   = "../modules/cloudwatch"
  for_each = toset(var.services)

  name_prefix         = local.name_prefix
  service_name        = each.value
  log_retention_days  = 1
  tags                = local.common_tags
}

# Application Load Balancer
module "alb" {
  source = "../modules/alb"

  name_prefix              = local.name_prefix
  vpc_id                   = module.vpc.vpc_id
  public_subnet_ids        = module.vpc.public_subnet_ids
  alb_security_group_id    = module.security_groups.alb_security_group_id
  services                 = var.services
  service_container_ports  = local.service_container_ports
  tags                     = local.common_tags
}

# ECS Cluster
module "ecs_cluster" {
  source = "../modules/ecs-cluster"

  cluster_name              = "${local.name_prefix}-cluster"
  service_connect_namespace = "medisupply.local"
  tags                      = local.common_tags
}

# ECR Repositories
module "ecr" {
  source   = "../modules/ecr"
  for_each = toset(var.services)

  repository_name      = each.value
  image_tag_mutability = "MUTABLE"
  scan_on_push         = true
  common_tags          = local.common_tags
}

# ECS Task Definitions (one per service)
module "ecs_task_definition" {
  source   = "../modules/ecs-task-definition"
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
  container_port       = local.service_container_ports[each.value]
  health_check_path    = local.service_health_check_paths[each.value]
  tags                 = local.common_tags
}

# ECS Services (one per service)
module "ecs_service" {
  source   = "../modules/ecs-service"
  for_each = toset(var.services)

  name_prefix                    = local.name_prefix
  service_name                   = each.value
  cluster_id                     = module.ecs_cluster.cluster_id
  task_definition_arn            = module.ecs_task_definition[each.value].task_definition_arn
  desired_count                  = 1
  subnet_ids                     = module.vpc.public_subnet_ids
  security_group_id              = module.security_groups.ecs_tasks_security_group_id
  target_group_arn               = module.alb.target_group_arns[each.value]
  container_port                 = local.service_container_ports[each.value]
  service_connect_namespace_arn  = module.ecs_cluster.service_connect_namespace_arn
  service_connect_namespace_name = module.ecs_cluster.service_connect_namespace_name
  tags                           = local.common_tags

  depends_on = [module.alb]
}

# RDS Databases - One for each microservice
# Using cheapest possible configuration (db.t3.micro, 20GB storage)

module "rds_catalog" {
  source = "../modules/rds"

  name_prefix        = local.name_prefix
  db_name            = "catalogdb2"
  master_password    = local.db_password
  private_subnet_ids = module.vpc.public_subnet_ids
  security_group_id  = module.security_groups.rds_security_group_id
  tags               = local.common_tags
}

module "rds_client" {
  source = "../modules/rds"

  name_prefix        = local.name_prefix
  db_name            = "client2"
  master_password    = local.db_password
  private_subnet_ids = module.vpc.public_subnet_ids
  security_group_id  = module.security_groups.rds_security_group_id
  tags               = local.common_tags
}

module "rds_delivery" {
  source = "../modules/rds"

  name_prefix        = local.name_prefix
  db_name            = "delivery2"
  master_password    = local.db_password
  private_subnet_ids = module.vpc.public_subnet_ids
  security_group_id  = module.security_groups.rds_security_group_id
  tags               = local.common_tags
}

module "rds_inventory" {
  source = "../modules/rds"

  name_prefix        = local.name_prefix
  db_name            = "inventory2"
  master_password    = local.db_password
  private_subnet_ids = module.vpc.public_subnet_ids
  security_group_id  = module.security_groups.rds_security_group_id
  tags               = local.common_tags
}

module "rds_order" {
  source = "../modules/rds"

  name_prefix        = local.name_prefix
  db_name            = "orderdb2"
  master_password    = local.db_password
  private_subnet_ids = module.vpc.public_subnet_ids
  security_group_id  = module.security_groups.rds_security_group_id
  tags               = local.common_tags
}

module "rds_seller" {
  source = "../modules/rds"

  name_prefix        = local.name_prefix
  db_name            = "seller2"
  master_password    = local.db_password
  private_subnet_ids = module.vpc.public_subnet_ids
  security_group_id  = module.security_groups.rds_security_group_id
  tags               = local.common_tags
}

locals {
  name_prefix = "medisupply"
  common_tags = {
    ManagedBy   = "terraform"
    Environment = "common"
  }
}

# Cognito Module for Authentication (shared across environments)
# Uses direct password authentication (USER_PASSWORD_AUTH) - no OAuth flows
module "cognito" {
  source = "../modules/cognito"

  name_prefix = local.name_prefix
  tags        = local.common_tags
}

# ECR Repositories (shared across environments)
module "ecr" {
  source   = "../modules/ecr"
  for_each = toset(var.services)

  repository_name      = each.value
  image_tag_mutability = "MUTABLE"
  scan_on_push         = true
  common_tags          = local.common_tags
}

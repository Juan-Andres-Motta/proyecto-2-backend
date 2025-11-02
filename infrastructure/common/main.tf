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

# S3 Buckets for Reports (shared across environments)
module "s3_order_reports" {
  source = "../modules/s3-reports-bucket"

  bucket_name = "${local.name_prefix}-order-reports"
  tags        = local.common_tags
}

module "s3_inventory_reports" {
  source = "../modules/s3-reports-bucket"

  bucket_name = "${local.name_prefix}-inventory-reports"
  tags        = local.common_tags
}

# S3 Bucket for Visit Evidence (shared across environments)
module "s3_evidence" {
  source = "../modules/s3-evidence-bucket"

  bucket_name = "${local.name_prefix}-evidence"
  tags        = local.common_tags
}

# SQS Queue for Report Events (shared across environments)
module "sqs_reports_queue" {
  source = "../modules/sqs-queue"

  queue_name = "${local.name_prefix}-reports-queue"
  tags       = local.common_tags
}

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

# SNS Topic for Order Events (shared across environments)
# Publishes events to multiple SQS queues using fanout pattern
module "sns_order_events_topic" {
  source = "../modules/sns-topic"

  topic_name = "${local.name_prefix}-order-events-topic"
  tags       = local.common_tags
}

# SQS Queue for Order Events - Seller Service Consumer
module "sqs_order_events_seller_queue" {
  source = "../modules/sqs-queue"

  queue_name = "${local.name_prefix}-order-events-seller-queue"
  tags       = merge(local.common_tags, { Consumer = "seller" })
}

# SQS Queue for Order Events - BFF Service Consumer
module "sqs_order_events_bff_queue" {
  source = "../modules/sqs-queue"

  queue_name = "${local.name_prefix}-order-events-bff-queue"
  tags       = merge(local.common_tags, { Consumer = "bff" })
}

# SNS to SQS Subscription - Seller Queue
module "sns_to_seller_subscription" {
  source = "../modules/sns-sqs-subscription"

  topic_arn            = module.sns_order_events_topic.topic_arn
  queue_arn            = module.sqs_order_events_seller_queue.queue_arn
  queue_url            = module.sqs_order_events_seller_queue.queue_url
  raw_message_delivery = true  # Deliver event payload without SNS wrapper
}

# SNS to SQS Subscription - BFF Queue
module "sns_to_bff_subscription" {
  source = "../modules/sns-sqs-subscription"

  topic_arn            = module.sns_order_events_topic.topic_arn
  queue_arn            = module.sqs_order_events_bff_queue.queue_arn
  queue_url            = module.sqs_order_events_bff_queue.queue_url
  raw_message_delivery = true  # Deliver event payload without SNS wrapper
}

# DEPRECATED: Old single queue (keep for migration, remove after cutover)
module "sqs_order_events_queue" {
  source = "../modules/sqs-queue"

  queue_name = "${local.name_prefix}-order-events-queue"
  tags       = merge(local.common_tags, { Status = "deprecated" })
}

# IAM resources including CI/CD user for ECR push
module "iam" {
  source = "../modules/iam"

  name_prefix = local.name_prefix
  tags        = local.common_tags

  # Pass all ECR repository ARNs for CI/CD push access
  ecr_repository_arns = [for repo in module.ecr : repo.repository_arn]
}

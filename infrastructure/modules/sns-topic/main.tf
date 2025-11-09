resource "aws_sns_topic" "topic" {
  name = var.topic_name

  # Enable server-side encryption
  kms_master_key_id = var.kms_master_key_id

  # Content-based deduplication for FIFO topics
  content_based_deduplication = var.fifo_topic ? true : null
  fifo_topic                  = var.fifo_topic

  tags = var.tags
}

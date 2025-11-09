resource "aws_sns_topic_subscription" "subscription" {
  topic_arn            = var.topic_arn
  protocol             = "sqs"
  endpoint             = var.queue_arn
  raw_message_delivery = var.raw_message_delivery
}

# Grant SNS permission to send messages to the SQS queue
resource "aws_sqs_queue_policy" "policy" {
  queue_url = var.queue_url

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowSNSPublish"
        Effect = "Allow"
        Principal = {
          Service = "sns.amazonaws.com"
        }
        Action   = "SQS:SendMessage"
        Resource = var.queue_arn
        Condition = {
          ArnEquals = {
            "aws:SourceArn" = var.topic_arn
          }
        }
      }
    ]
  })
}

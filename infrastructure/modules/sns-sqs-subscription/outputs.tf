output "subscription_arn" {
  description = "ARN of the SNS subscription"
  value       = aws_sns_topic_subscription.subscription.arn
}

output "subscription_id" {
  description = "ID of the SNS subscription"
  value       = aws_sns_topic_subscription.subscription.id
}

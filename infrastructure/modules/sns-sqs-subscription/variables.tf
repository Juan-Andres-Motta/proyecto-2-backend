variable "topic_arn" {
  description = "ARN of the SNS topic"
  type        = string
}

variable "queue_arn" {
  description = "ARN of the SQS queue"
  type        = string
}

variable "queue_url" {
  description = "URL of the SQS queue"
  type        = string
}

variable "raw_message_delivery" {
  description = "Whether to enable raw message delivery (true = no SNS envelope)"
  type        = bool
  default     = true
}

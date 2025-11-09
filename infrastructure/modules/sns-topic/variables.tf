variable "topic_name" {
  description = "Name of the SNS topic"
  type        = string
}

variable "fifo_topic" {
  description = "Whether the topic is FIFO"
  type        = bool
  default     = false
}

variable "kms_master_key_id" {
  description = "KMS key ID for encryption (optional)"
  type        = string
  default     = null
}

variable "allowed_publishers" {
  description = "List of AWS services allowed to publish to this topic"
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Tags to apply to the topic"
  type        = map(string)
  default     = {}
}

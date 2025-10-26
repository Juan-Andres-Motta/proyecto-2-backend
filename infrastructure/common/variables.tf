variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "services" {
  description = "List of microservices"
  type        = list(string)
  default     = ["bff", "catalog", "client", "delivery", "inventory", "order", "seller"]
}

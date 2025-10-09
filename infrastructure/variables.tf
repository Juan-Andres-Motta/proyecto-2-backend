variable "aws_region" {
  description = "AWS region where resources will be created"
  type        = string
  default     = "us-east-1"
}

variable "services" {
  description = "List of microservices that need ECR repositories"
  type        = list(string)
  default = [
    "bff",
    "catalog",
    "client",
    "delivery",
    "inventory",
    "order",
    "seller"
  ]
}

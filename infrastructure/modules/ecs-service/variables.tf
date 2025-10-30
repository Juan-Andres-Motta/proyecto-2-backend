variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "service_name" {
  description = "Name of the service"
  type        = string
}

variable "cluster_id" {
  description = "ID of the ECS cluster"
  type        = string
}

variable "task_definition_arn" {
  description = "ARN of the task definition"
  type        = string
}

variable "desired_count" {
  description = "Desired number of tasks"
  type        = number
  default     = 1
}

variable "subnet_ids" {
  description = "IDs of subnets for the service"
  type        = list(string)
}

variable "security_group_id" {
  description = "ID of the security group for ECS tasks"
  type        = string
}

variable "target_group_arn" {
  description = "ARN of the ALB target group (optional)"
  type        = string
  default     = null
}

variable "container_port" {
  description = "Port the container listens on"
  type        = number
  default     = 8000
}

variable "service_connect_namespace_arn" {
  description = "ARN of the Service Connect namespace"
  type        = string
}

variable "service_connect_namespace_name" {
  description = "Name of the Service Connect namespace"
  type        = string
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}

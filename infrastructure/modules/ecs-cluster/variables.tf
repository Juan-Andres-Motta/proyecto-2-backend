variable "cluster_name" {
  description = "Name of the ECS cluster"
  type        = string
}

variable "service_connect_namespace" {
  description = "Service Connect namespace for internal communication"
  type        = string
  default     = "medisupply.local"
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}

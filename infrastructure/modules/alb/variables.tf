variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "public_subnet_ids" {
  description = "IDs of public subnets for ALB"
  type        = list(string)
}

variable "alb_security_group_id" {
  description = "ID of the ALB security group"
  type        = string
}

variable "services" {
  description = "List of service names"
  type        = list(string)
}

variable "service_container_ports" {
  description = "Map of service names to their container ports"
  type        = map(number)
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}

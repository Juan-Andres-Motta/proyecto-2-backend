variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "db_name" {
  description = "Name of the database"
  type        = string
}

variable "engine_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "15.14"
}

variable "instance_class" {
  description = "Instance class for RDS (free tier: db.t3.micro)"
  type        = string
  default     = "db.t3.micro"
}

variable "allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 20
}

variable "max_allocated_storage" {
  description = "Maximum storage for autoscaling in GB"
  type        = number
  default     = 100
}

variable "master_username" {
  description = "Master username for the database"
  type        = string
  default     = "postgres"
}

variable "master_password" {
  description = "Master password for the database"
  type        = string
  sensitive   = true
}

variable "private_subnet_ids" {
  description = "IDs of subnets for RDS (can be public or private)"
  type        = list(string)
}

variable "security_group_id" {
  description = "ID of the security group for RDS"
  type        = string
}

variable "backup_retention_period" {
  description = "Number of days to retain backups"
  type        = number
  default     = 7
}

variable "multi_az" {
  description = "Enable Multi-AZ for high availability"
  type        = bool
  default     = false
}

variable "deletion_protection" {
  description = "Enable deletion protection"
  type        = bool
  default     = false
}

variable "skip_final_snapshot" {
  description = "Skip final snapshot on deletion"
  type        = bool
  default     = true
}

variable "enable_cloudwatch_logs" {
  description = "Enable CloudWatch logs export"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}

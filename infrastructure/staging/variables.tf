variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type for staging"
  type        = string
  default     = "t3.medium"  # 2 vCPU, 4GB RAM
}

variable "key_name" {
  description = "SSH key pair name for EC2 access"
  type        = string
  # Set this when running terraform apply: -var="key_name=your-key"
}

variable "allowed_ssh_cidr" {
  description = "CIDR blocks allowed to SSH into the instance"
  type        = list(string)
  default     = ["0.0.0.0/0"]  # Update to your IP for security
}

variable "volume_size" {
  description = "Root volume size in GB"
  type        = number
  default     = 30
}

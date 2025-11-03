variable "bucket_name" {
  description = "Name of the S3 bucket for visit evidence"
  type        = string
}

variable "allowed_origins" {
  description = "List of allowed CORS origins for presigned uploads"
  type        = list(string)
  default     = ["*"]
}

variable "tags" {
  description = "Tags to apply to the S3 bucket"
  type        = map(string)
  default     = {}
}

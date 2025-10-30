variable "bucket_name" {
  description = "Name of the S3 bucket for reports"
  type        = string
}

variable "allowed_origins" {
  description = "List of allowed origins for CORS"
  type        = list(string)
  default = [
    "http://localhost:3000",
    "https://localhost:3000",
    "https://bffproyecto.juanandresdeveloper.com",
    "https://*.medisupply.andres-duque.com"
  ]
}

variable "tags" {
  description = "Tags to apply to the S3 bucket"
  type        = map(string)
  default     = {}
}

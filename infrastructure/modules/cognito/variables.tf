variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "web_callback_urls" {
  description = "Allowed callback URLs for web application"
  type        = list(string)
  default     = ["http://localhost:3000/callback", "https://localhost:3000/callback"]
}

variable "web_logout_urls" {
  description = "Allowed logout URLs for web application"
  type        = list(string)
  default     = ["http://localhost:3000/", "https://localhost:3000/"]
}

variable "mobile_callback_urls" {
  description = "Allowed callback URLs for mobile application (deep links)"
  type        = list(string)
  default     = ["medisupply://callback"]
}

variable "mobile_logout_urls" {
  description = "Allowed logout URLs for mobile application"
  type        = list(string)
  default     = ["medisupply://logout"]
}

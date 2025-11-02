output "bucket_name" {
  description = "Name of the S3 evidence bucket"
  value       = aws_s3_bucket.evidence.id
}

output "bucket_arn" {
  description = "ARN of the S3 evidence bucket"
  value       = aws_s3_bucket.evidence.arn
}

output "bucket_domain_name" {
  description = "Domain name of the S3 evidence bucket"
  value       = aws_s3_bucket.evidence.bucket_domain_name
}

output "bucket_regional_domain_name" {
  description = "Regional domain name of the S3 evidence bucket"
  value       = aws_s3_bucket.evidence.bucket_regional_domain_name
}

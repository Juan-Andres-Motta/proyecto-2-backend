output "cluster_id" {
  description = "ID of the ECS cluster"
  value       = aws_ecs_cluster.main.id
}

output "cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = aws_ecs_cluster.main.arn
}

output "service_connect_namespace_arn" {
  description = "ARN of the Service Connect namespace"
  value       = aws_service_discovery_http_namespace.main.arn
}

output "service_connect_namespace_name" {
  description = "Name of the Service Connect namespace"
  value       = aws_service_discovery_http_namespace.main.name
}

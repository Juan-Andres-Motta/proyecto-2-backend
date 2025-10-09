# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = var.cluster_name

  setting {
    name  = "containerInsights"
    value = "disabled" # Disabled to save costs
  }

  tags = var.tags
}

# ECS Cluster Capacity Providers (FARGATE and FARGATE_SPOT)
resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name = aws_ecs_cluster.main.name

  capacity_providers = ["FARGATE", "FARGATE_SPOT"]

  default_capacity_provider_strategy {
    capacity_provider = "FARGATE_SPOT"
    weight            = 100
    base              = 0
  }
}

# Service Connect Namespace (for internal service-to-service communication)
resource "aws_service_discovery_http_namespace" "main" {
  name        = var.service_connect_namespace
  description = "Service Connect namespace for ${var.cluster_name}"

  tags = var.tags
}

resource "aws_ecs_service" "service" {
  name            = "${var.name_prefix}-${var.service_name}-service"
  cluster         = var.cluster_id
  task_definition = var.task_definition_arn
  desired_count   = var.desired_count

  # Use FARGATE_SPOT for cost savings
  capacity_provider_strategy {
    capacity_provider = "FARGATE_SPOT"
    weight            = 100
    base              = 0
  }

  network_configuration {
    subnets          = var.subnet_ids
    security_groups  = [var.security_group_id]
    assign_public_ip = true # Required for pulling from ECR without NAT Gateway
  }

  # Load balancer configuration (optional)
  dynamic "load_balancer" {
    for_each = var.target_group_arn != null ? [1] : []
    content {
      target_group_arn = var.target_group_arn
      container_name   = var.service_name
      container_port   = var.container_port
    }
  }

  # Service Connect configuration for internal service-to-service communication
  service_connect_configuration {
    enabled   = true
    namespace = var.service_connect_namespace_arn

    service {
      port_name = var.service_name

      client_alias {
        port     = var.container_port
        dns_name = "${var.service_name}.${var.service_connect_namespace_name}"
      }
    }
  }

  # Deployment settings - top level arguments per AWS provider v6.x
  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200

  # Circuit breaker for automatic rollback on deployment failure
  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  # Health check grace period for ALB (only when using load balancer)
  health_check_grace_period_seconds = var.target_group_arn != null ? 60 : null

  # Wait for steady state before considering deployment complete
  wait_for_steady_state = true  # Changed to true for safer deployments

  # Ignore changes to desired_count (for auto-scaling)
  lifecycle {
    ignore_changes = [desired_count]
  }

  tags = merge(
    var.tags,
    {
      Name    = "${var.name_prefix}-${var.service_name}-service"
      Service = var.service_name
    }
  )
}

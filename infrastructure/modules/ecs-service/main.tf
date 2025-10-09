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

  # Load balancer configuration
  load_balancer {
    target_group_arn = var.target_group_arn
    container_name   = var.service_name
    container_port   = var.container_port
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

  # Native ECS Blue/Green Deployment (supports Service Connect!)
  deployment_configuration {
    deployment_type = "BLUE_GREEN"

    blue_green_deployment_config {
      # Traffic routing configuration
      traffic_routing {
        type = "ALL_AT_ONCE"  # Can also be "TIME_BASED_CANARY" or "TIME_BASED_LINEAR"
      }

      # Termination configuration for original (blue) tasks
      terminate_blue_tasks_on_deployment_success {
        action                   = "TERMINATE"
        termination_wait_time_in_minutes = 5  # Wait 5 minutes before terminating blue tasks
      }

      # Deployment success criteria
      deployment_ready_option {
        action_on_timeout = "STOP_DEPLOYMENT"  # Stop if deployment doesn't complete in time
        wait_time_in_minutes = 10               # Wait up to 10 minutes for deployment to be ready
      }
    }

    # Deployment circuit breaker (rollback on failure)
    deployment_circuit_breaker {
      enable   = true
      rollback = true
    }

    # Minimum healthy percent during deployment
    minimum_healthy_percent = 100

    # Maximum percent during deployment
    maximum_percent = 200
  }

  # Health check grace period for ALB
  health_check_grace_period_seconds = 60

  # Wait for steady state before considering deployment complete
  wait_for_steady_state = false

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

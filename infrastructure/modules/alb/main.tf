# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${var.name_prefix}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [var.alb_security_group_id]
  subnets            = var.public_subnet_ids

  enable_deletion_protection = false
  enable_http2              = true

  tags = merge(
    var.tags,
    {
      Name = "${var.name_prefix}-alb"
    }
  )
}

# Target Groups - one per service
resource "aws_lb_target_group" "service" {
  for_each = toset(var.services)

  name        = "${var.name_prefix}-${each.value}-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/${each.value}/health"
    matcher             = "200"
  }

  deregistration_delay = 30

  tags = merge(
    var.tags,
    {
      Name    = "${var.name_prefix}-${each.value}-tg"
      Service = each.value
    }
  )
}

# HTTP Listener
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  # Default action - return 404
  default_action {
    type = "fixed-response"
    fixed_response {
      content_type = "text/plain"
      message_body = "Service not found"
      status_code  = "404"
    }
  }

  tags = var.tags
}

# Listener Rules - path-based routing for each service
resource "aws_lb_listener_rule" "service" {
  for_each = toset(var.services)

  listener_arn = aws_lb_listener.http.arn
  priority     = index(var.services, each.value) + 1

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.service[each.value].arn
  }

  condition {
    path_pattern {
      values = ["/${each.value}/*"]
    }
  }

  tags = merge(
    var.tags,
    {
      Service = each.value
    }
  )
}

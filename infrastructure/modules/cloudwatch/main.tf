resource "aws_cloudwatch_log_group" "ecs_service" {
  name              = "/ecs/${var.name_prefix}/${var.service_name}"
  retention_in_days = var.log_retention_days

  tags = merge(
    var.tags,
    {
      Name    = "${var.name_prefix}-${var.service_name}-logs"
      Service = var.service_name
    }
  )
}

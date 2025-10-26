# EC2 Instance Outputs
output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.staging.id
}

output "instance_public_ip" {
  description = "EC2 instance public IP"
  value       = aws_eip.staging.public_ip
}

output "instance_public_dns" {
  description = "EC2 instance public DNS"
  value       = aws_instance.staging.public_dns
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh -i ~/.ssh/${var.key_name}.pem ec2-user@${aws_eip.staging.public_ip}"
}

# Service URLs
output "bff_url" {
  description = "BFF service URL"
  value       = "http://${aws_eip.staging.public_ip}:8000/bff"
}

output "catalog_url" {
  description = "Catalog service URL"
  value       = "http://${aws_eip.staging.public_ip}:8001/catalog"
}

output "client_url" {
  description = "Client service URL"
  value       = "http://${aws_eip.staging.public_ip}:8002/client"
}

output "delivery_url" {
  description = "Delivery service URL"
  value       = "http://${aws_eip.staging.public_ip}:8003/delivery"
}

output "inventory_url" {
  description = "Inventory service URL"
  value       = "http://${aws_eip.staging.public_ip}:8004/inventory"
}

output "order_url" {
  description = "Order service URL"
  value       = "http://${aws_eip.staging.public_ip}:8005/order"
}

output "seller_url" {
  description = "Seller service URL"
  value       = "http://${aws_eip.staging.public_ip}:8006/seller"
}

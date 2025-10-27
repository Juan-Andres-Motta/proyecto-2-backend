#!/bin/bash
set -e

echo "=== MediSupply Staging Deployment Script ==="
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI is not installed"
    exit 1
fi

# Get ECR repository URLs from common terraform outputs
echo "1. Getting ECR repository URLs..."
cd ../common
if [ ! -d ".terraform" ]; then
    echo "Error: Common resources not provisioned. Run 'terraform init && terraform apply' in infrastructure/common first"
    exit 1
fi

# Export ECR URLs
export ECR_BFF_REPO=$(terraform output -json ecr_repository_urls | jq -r '.bff')
export ECR_CATALOG_REPO=$(terraform output -json ecr_repository_urls | jq -r '.catalog')
export ECR_CLIENT_REPO=$(terraform output -json ecr_repository_urls | jq -r '.client')
export ECR_DELIVERY_REPO=$(terraform output -json ecr_repository_urls | jq -r '.delivery')
export ECR_INVENTORY_REPO=$(terraform output -json ecr_repository_urls | jq -r '.inventory')
export ECR_ORDER_REPO=$(terraform output -json ecr_repository_urls | jq -r '.order')
export ECR_SELLER_REPO=$(terraform output -json ecr_repository_urls | jq -r '.seller')

# Export AWS resource URLs
export AWS_REGION=us-east-1
export SQS_QUEUE_URL=$(terraform output -raw sqs_reports_queue_url)
export SQS_REGION=us-east-1
export SQS_REPORTS_QUEUE_URL=$(terraform output -raw sqs_reports_queue_url)
export S3_REPORTS_BUCKET=$(terraform output -raw s3_order_reports_bucket_name)
export S3_ORDER_REPORTS_BUCKET=$(terraform output -raw s3_order_reports_bucket_name)
export S3_INVENTORY_REPORTS_BUCKET=$(terraform output -raw s3_inventory_reports_bucket_name)

echo "ECR repositories loaded"
echo ""

# Login to ECR
echo "2. Logging into ECR..."
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=${AWS_REGION:-us-east-1}
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

echo ""
echo "3. Starting services with Docker Compose..."
cd ../staging
docker-compose pull
docker-compose up -d

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Services are starting up. Check status with:"
echo "  docker-compose ps"
echo ""
echo "View logs with:"
echo "  docker-compose logs -f [service-name]"
echo ""
echo "Access services at:"
echo "  BFF: http://$(terraform output -raw instance_public_ip 2>/dev/null || echo "INSTANCE_IP"):8000/bff"
echo "  Catalog: http://$(terraform output -raw instance_public_ip 2>/dev/null || echo "INSTANCE_IP"):8001/catalog"
echo ""

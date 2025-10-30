# MediSupply Infrastructure

This directory contains all infrastructure code for deploying MediSupply across different environments.

## Structure

```
infrastructure/
├── common/              # Shared AWS resources (ECR, Cognito)
├── staging/             # Staging environment (EC2 + Docker Compose)
├── production/          # Production environment (ECS + RDS)
└── modules/             # Reusable Terraform modules
```

## Deployment Order

### 1. Common Resources (Run Once)

These resources are shared between staging and production:
- **ECR Repositories**: Docker image storage
- **Cognito**: User authentication

```bash
cd common
terraform init
terraform apply

# Save outputs to .env.common
terraform output cognito_user_pool_id >> .env.common
terraform output cognito_web_client_id >> .env.common
terraform output cognito_mobile_client_id >> .env.common
terraform output ecr_repository_urls >> .env.common
```

### 2. Staging Environment

Staging runs on a single EC2 instance with Docker Compose:

```bash
cd staging

# 1. Provision EC2 infrastructure
terraform init
terraform apply -var="key_name=your-ssh-key"

# 2. Get EC2 IP
EC2_IP=$(terraform output -raw instance_public_ip)

# 3. SSH to EC2
ssh -i ~/.ssh/your-key.pem ec2-user@$EC2_IP

# 4. On EC2: Clone repo and deploy
git clone https://github.com/your-org/proyecto-2-backend.git
cd proyecto-2-backend/infrastructure/staging
./deploy.sh
```

### 3. Production Environment

Production uses ECS Fargate with RDS databases:

```bash
cd production

# 1. Create DB password secret
aws secretsmanager create-secret \
  --name medisupply-db-password \
  --secret-string "your-secure-password"

# 2. Deploy infrastructure
terraform init
terraform apply

# 3. Build and push images to ECR
# (Use GitHub Actions or manual push)

# 4. Run migrations
./run-migration.sh
```

## Environment Comparison

| Resource | Staging | Production |
|----------|---------|------------|
| Compute | EC2 (t3.medium) | ECS Fargate |
| Database | Docker PostgreSQL | RDS PostgreSQL |
| Networking | Single EC2 | ALB + Service Connect |
| Cost | ~$30/month | ~$200/month |
| Use Case | Testing, demos | Customer-facing |

## Common Resources

### Cognito
- **User Pool**: Shared authentication using direct password authentication (USER_PASSWORD_AUTH)
- **Web Client**: For web applications (no OAuth flows)
- **Mobile Client**: For mobile apps (no OAuth flows)
- **User Groups**: web_users, seller_users, client_users

### ECR Repositories
All container images are stored in ECR and shared:
- `bff`
- `catalog`
- `client`
- `delivery`
- `inventory`
- `order`
- `seller`

## Configuration Files

### common/.env.common
Shared configuration (Cognito, ECR URLs, AWS region)

### staging/.env.staging
Staging-specific settings (log levels, debug flags)

### staging/docker-compose.yml
All services + databases for EC2 deployment

## Useful Commands

### Staging

```bash
# View logs
ssh ec2-user@$EC2_IP
cd ~/proyecto-2-backend/infrastructure/staging
docker-compose logs -f bff

# Restart service
docker-compose restart bff

# Pull latest images
docker-compose pull
docker-compose up -d

# Stop all services
docker-compose down
```

### Production

```bash
# Update service
aws ecs update-service \
  --cluster medisupply-cluster \
  --service medisupply-bff \
  --force-new-deployment

# View logs
aws logs tail /ecs/medisupply-bff --follow

# Run migration
./run-migration.sh
```

## Troubleshooting

### Staging: Can't connect to EC2
- Check security group allows your IP
- Verify key pair name matches
- Check instance status: `aws ec2 describe-instances`

### Production: ECS tasks failing
- Check task logs in CloudWatch
- Verify secrets exist in Secrets Manager
- Check RDS security group allows ECS tasks

### Both: Can't pull images
- Login to ECR: `aws ecr get-login-password | docker login ...`
- Verify images exist: `aws ecr list-images --repository-name bff`

## Cost Optimization

- Staging EC2 can be stopped when not in use
- Use t3.micro for lower traffic in staging
- Production RDS in public subnets to save NAT costs (current setup)
- Consider IPv6 to reduce IPv4 charges

## Security Notes

- RDS is in public subnets (intentional for cost savings)
- Ensure security groups properly restrict access
- Rotate database passwords regularly
- Use IAM roles instead of access keys where possible

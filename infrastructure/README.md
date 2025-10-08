# Medisupply Infrastructure

Complete Terraform infrastructure for deploying the Medisupply microservices platform on AWS ECS Fargate.

## Architecture Overview

```
Internet
    ↓
Application Load Balancer (ALB)
    ↓ (path-based routing)
ECS Cluster (Fargate SPOT)
    ├── BFF Service
    ├── Catalog Service
    ├── Client Service
    ├── Delivery Service
    ├── Inventory Service
    ├── Order Service
    └── Seller Service
    ↓ (Service Connect for internal communication)
    ↓
RDS PostgreSQL (private subnets - NOT deployed yet)
```

## Cost Optimization Features

- ✅ **FARGATE_SPOT** (70% discount on compute)
- ✅ **Minimum CPU/Memory** (0.25 vCPU / 0.5 GB per task)
- ✅ **1-day log retention** (vs 30 days default)
- ✅ **No NAT Gateway** (saves ~$32/month)
- ✅ **No CloudWatch alarms** (saves ~$3/month)
- ✅ **No WAF** (saves ~$5-10/month)
- ✅ **Deployment rollback only during deployment** (Circuit Breaker)

**Estimated Cost:** ~$42-50/month for 7 services

## Infrastructure Modules

### Core Networking
- **VPC**: 10.0.0.0/16 with public and private subnets
- **Internet Gateway**: For public internet access
- **Security Groups**: ALB, ECS tasks, and RDS

### Compute
- **ECS Cluster**: `medisupply-cluster` with FARGATE_SPOT
- **Service Connect**: `medisupply.local` namespace for internal communication
- **7 ECS Services**: One per microservice (1 task each, max 2)

### Networking & Load Balancing
- **Application Load Balancer**: Path-based routing (`/bff/*`, `/catalog/*`, etc.)
- **Target Groups**: Health checks on `/health` endpoint

### Logging & Monitoring
- **CloudWatch Log Groups**: 1-day retention per service
- **ECS Circuit Breaker**: Automatic rollback on deployment failure (5% threshold)

### Container Registry
- **ECR Repositories**: One per service with lifecycle policy (max 4 images)

### Database (Module Created, NOT Applied)
- **RDS Module**: PostgreSQL free tier configuration
- Located in `modules/rds/` but commented out in `main.tf`

## Prerequisites

1. **AWS CLI** configured with credentials
2. **Terraform** >= 1.0
3. **Docker images** built and ready to push to ECR

## Deployment Steps

### 1. Initialize Terraform

```bash
cd infrastructure
terraform init
```

### 2. Review the Plan

```bash
terraform plan
```

### 3. Deploy Infrastructure

```bash
terraform apply
```

**Note:** Initial deployment will FAIL because Docker images don't exist in ECR yet. This is expected.

### 4. Build and Push Docker Images

After infrastructure is created, you'll have ECR repositories. Build and push your images:

```bash
# Get ECR login
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and push each service
cd ../bff
docker build -t bff .
docker tag bff:latest <ecr-repo-url>/bff:latest
docker push <ecr-repo-url>/bff:latest

# Repeat for all services: catalog, client, delivery, inventory, order, seller
```

**Tip:** Use the GitHub Actions workflow to automate this:
```bash
git push origin main
# GitHub Actions will build and push images automatically
```

### 5. Re-deploy with Images

```bash
cd infrastructure
terraform apply
```

ECS services will now start successfully with your Docker images.

### 6. Test the Deployment

```bash
# Get ALB URL from outputs
terraform output alb_url

# Test individual service
curl http://<alb-dns-name>/catalog/health

# Test internal communication
curl http://<alb-dns-name>/bff/check-all
```

Expected response from `/bff/check-all`:
```json
[
  {"catalog": "healthy"},
  {"client": "healthy"},
  {"delivery": "healthy"},
  {"inventory": "healthy"},
  {"order": "healthy"},
  {"seller": "healthy"}
]
```

## Service URLs

All services are accessible via the ALB with path-based routing:

```
http://<alb-dns-name>/bff/
http://<alb-dns-name>/catalog/
http://<alb-dns-name>/client/
http://<alb-dns-name>/delivery/
http://<alb-dns-name>/inventory/
http://<alb-dns-name>/order/
http://<alb-dns-name>/seller/
```

## Internal Communication (Service Connect)

Services communicate internally using Service Connect DNS:

```
http://bff.medisupply.local:8000
http://catalog.medisupply.local:8000
http://client.medisupply.local:8000
http://delivery.medisupply.local:8000
http://inventory.medisupply.local:8000
http://order.medisupply.local:8000
http://seller.medisupply.local:8000
```

## Environment Variables

Environment variables are defined in `main.tf` under `locals.service_env_vars`:

### BFF
- `CATALOG_URL`, `CLIENT_URL`, `DELIVERY_URL`, `INVENTORY_URL`, `ORDER_URL`, `SELLER_URL`

### Services with Databases
- `DATABASE_URL` (currently set to localhost, update when RDS is deployed)

## Deployment Rollback

ECS Circuit Breaker is enabled with automatic rollback:
- If >5% of tasks fail health checks during deployment → automatic rollback
- Only monitors during deployment (no ongoing alarms = cost savings)

## Viewing Logs

```bash
# View logs for a service
aws logs tail /ecs/medisupply/<service-name> --follow

# Example
aws logs tail /ecs/medisupply/catalog --follow
```

## Scaling Services

To manually scale a service:

```bash
aws ecs update-service \
  --cluster medisupply-cluster \
  --service medisupply-catalog-service \
  --desired-count 2
```

## Destroying Infrastructure

**Warning:** This will delete all resources.

```bash
terraform destroy
```

## Adding RDS Databases

When ready to add PostgreSQL databases:

1. Edit `main.tf` and uncomment the RDS module section
2. Update `DATABASE_URL` environment variables to point to RDS
3. Run `terraform apply`

Example for catalog service:
```hcl
module "rds_catalog" {
  source = "./modules/rds"

  name_prefix        = "medisupply"
  db_name            = "catalog"
  master_username    = "postgres"
  master_password    = var.db_password # Store in AWS Secrets Manager
  private_subnet_ids = module.vpc.private_subnet_ids
  security_group_id  = module.security_groups.rds_security_group_id
  tags               = local.common_tags
}
```

Then update the environment variable:
```hcl
catalog = {
  DATABASE_URL = "postgresql://postgres:${var.db_password}@${module.rds_catalog.db_instance_address}:5432/catalog"
  LOG_LEVEL    = "INFO"
  DEBUG_SQL    = "false"
}
```

## Troubleshooting

### Tasks not starting
```bash
# Check service events
aws ecs describe-services --cluster medisupply-cluster --services medisupply-catalog-service

# Check task logs
aws logs tail /ecs/medisupply/catalog --follow
```

### Health checks failing
- Ensure your service has a `/health` endpoint that returns `{"status": "ok"}`
- Check security group allows ALB → ECS on port 8000

### Image pull errors
- Ensure Docker images are pushed to ECR
- Verify task execution role has ECR permissions

## Useful Commands

```bash
# List all services
aws ecs list-services --cluster medisupply-cluster

# Describe a service
aws ecs describe-services --cluster medisupply-cluster --services medisupply-bff-service

# List running tasks
aws ecs list-tasks --cluster medisupply-cluster

# Get ALB DNS
terraform output alb_dns_name

# Get all service URLs
terraform output service_urls
```

## Module Structure

```
infrastructure/
├── modules/
│   ├── alb/                  # Application Load Balancer
│   ├── cloudwatch/           # Log groups
│   ├── ecr/                  # Container registry
│   ├── ecs-cluster/          # ECS cluster + Service Connect
│   ├── ecs-service/          # ECS service definition
│   ├── ecs-task-definition/  # Task definition
│   ├── iam/                  # IAM roles
│   ├── rds/                  # RDS PostgreSQL (not applied)
│   ├── security-groups/      # Network security
│   └── vpc/                  # VPC and networking
├── main.tf                   # Root configuration
├── variables.tf              # Input variables
├── outputs.tf                # Output values
├── providers.tf              # AWS provider config
└── terraform.tfvars          # Variable values
```

## Security Notes

- ECS tasks run in public subnets (to avoid NAT Gateway costs)
- Security groups restrict traffic to/from ALB only
- RDS databases will be in private subnets (no internet access)
- No public IPs on RDS instances

## Support

For issues or questions about the infrastructure, refer to:
- AWS ECS Documentation: https://docs.aws.amazon.com/ecs/
- Terraform AWS Provider: https://registry.terraform.io/providers/hashicorp/aws/

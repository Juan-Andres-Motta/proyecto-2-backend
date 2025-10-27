# Merge Plan: martin/reports → develop

## Executive Summary

**Goal**: Merge reports functionality and infrastructure from `martin/reports` into `develop` branch while preserving recent test coverage fixes and infrastructure restructuring.

**Challenge**: Major infrastructure restructuring occurred in `develop` (moved from monolithic `infrastructure/main.tf` to split `common/`, `staging/`, `production/` structure) while `martin/reports` has reports functionality based on the old monolithic structure.

**Recommendation**: Create a new integration branch and perform structured merge with manual conflict resolution.

---

## Branch Analysis

### Commit Divergence

**martin/reports unique commits** (6 commits ahead):
- `732139c` - reports
- `faccfa1` - updated test coverage
- `c384c51` - updated test
- `d331bd3` - updated sonar config
- `2740663` - feature/async-lister-publisher
- `5cccf28` - feature/authentication-&-authorization-&-registration (#20)

**develop unique commits** (12 commits ahead):
- `df490ba` through `722e7ff` - Multiple test coverage fixes (7 commits)
- `639fa5c` - Martin/stg setup (#24) **← Infrastructure restructure**
- `4f6bdb4` - Martin/client creation (#23)
- `78b9dc6` - feat/real-time-setup (#21)
- Plus others

**Common ancestor**: `3f66b29e31670ad9dc51995107c86eeb7a60d3f3`

### File Changes Summary

**Total changed files**: 96
- **Modified**: 31 files
- **Added**: 65 files

---

## Critical Conflicts

### 1. Infrastructure Structure Conflict (MAJOR)

**martin/reports** has:
```
infrastructure/
├── main.tf              # Monolithic, includes S3 + SQS + Cognito + all services
├── modules/
│   ├── cognito/
│   ├── s3-reports-bucket/  # NEW - Reports S3 buckets
│   └── sqs-queue/          # NEW - Reports SQS queue
└── staging/
```

**develop** has:
```
infrastructure/
├── common/
│   └── main.tf          # Only Cognito + ECR (NO S3, NO SQS)
├── production/
│   └── main.tf          # Full production infrastructure
└── staging/
    └── main.tf          # Staging infrastructure
```

**Conflict**:
- `martin/reports` has `infrastructure/main.tf` as the main file
- `develop` **deleted** `infrastructure/main.tf` and split into `common/`, `production/`, `staging/`
- Reports modules (`s3-reports-bucket/`, `sqs-queue/`) don't exist in `develop`

**Resolution Strategy**:
1. Keep `develop`'s split structure
2. Add S3 and SQS modules to `infrastructure/common/main.tf`
3. Copy reports modules to `infrastructure/modules/`
4. Update `production/main.tf` to use S3/SQS from common infrastructure

---

### 2. SonarCloud Workflow Conflict (MEDIUM)

**Both branches modified** `.github/workflows/sonarcloud.yml`:

**martin/reports changes**:
- Old sed pattern: `sed -i 's|<source>.*</source>|<source>/home/runner/work/...</source>|g'`
- Uses absolute paths for source tags

**develop changes** (CORRECT - fixes 0% coverage issue):
- New sed pattern: `sed -i 's|<source>.*</source>|<source>.</source>|g'`
- Fixed Order/Client paths: `sed -i 's|filename="|filename="order/src/|g'`
- Removed `develop` from push triggers (avoid duplicate runs)

**Resolution**: Keep `develop` version (it has the fixes we implemented)

---

### 3. BFF Application Structure (MEDIUM)

**Both branches modified**:
- `bff/app.py`
- `bff/dependencies.py`
- `bff/config/settings.py`

**martin/reports adds**:
- `bff/web/adapters/reports_adapter.py`
- `bff/web/controllers/reports_controller.py`
- Reports endpoints and schemas

**develop adds**:
- Client creation functionality
- Updated auth dependencies
- Common modules restructuring

**Resolution**: Manual merge required - need to integrate reports endpoints into develop's structure

---

### 4. Order Microservice (MEDIUM)

**Both branches modified**:
- `order/app.py`
- `order/src/adapters/input/schemas.py`
- `order/src/domain/value_objects.py`
- `order/src/infrastructure/database/models/__init__.py`

**martin/reports adds**:
- `order/src/adapters/input/controllers/reports_controller.py`
- `order/src/infrastructure/database/models/report.py`
- `order/alembic/versions/a5d4684abb15_2025_10_24_add_reports_table.py`
- Report use cases and domain logic

**Resolution**: Manual merge - add reports functionality to existing structure

---

### 5. Inventory Microservice (MEDIUM)

**Both branches modified**:
- `inventory/src/infrastructure/database/models/__init__.py`

**martin/reports adds**:
- `inventory/src/infrastructure/database/models/report.py`
- `inventory/alembic/versions/04c5aec22c99_2025_10_24_add_reports_table.py`

**Resolution**: Manual merge - add reports models

---

## Merge Strategy

### Option A: Feature Branch Integration (RECOMMENDED)

Create a new integration branch to carefully merge changes:

```bash
# 1. Create integration branch from develop
git checkout develop
git checkout -b feature/reports-integration

# 2. Attempt merge from martin/reports
git merge martin/reports --no-commit --no-ff

# 3. Resolve conflicts manually (see resolution steps below)

# 4. Test thoroughly before merging to develop
```

**Advantages**:
- Safe - doesn't break develop
- Allows thorough testing
- Can be reviewed before final merge
- Easy to abandon if issues arise

---

### Option B: Cherry-pick Reports Commits (ALTERNATIVE)

If conflicts are too severe, cherry-pick only reports functionality:

```bash
# 1. Create feature branch from develop
git checkout develop
git checkout -b feature/reports-cherry-pick

# 2. Cherry-pick only the reports commit
git cherry-pick 732139c

# 3. Manually resolve infrastructure conflicts
# 4. Adapt reports code to new infrastructure structure
```

---

## Step-by-Step Resolution Plan

### Phase 1: Infrastructure Resolution

#### Step 1.1: Add Reports Modules to develop
```bash
# Copy S3 and SQS modules from martin/reports
git checkout martin/reports -- infrastructure/modules/s3-reports-bucket/
git checkout martin/reports -- infrastructure/modules/sqs-queue/
```

#### Step 1.2: Update infrastructure/common/main.tf
Add to `infrastructure/common/main.tf`:
```terraform
# S3 Buckets for Reports (shared across environments)
module "s3_order_reports" {
  source = "../modules/s3-reports-bucket"

  bucket_name = "${local.name_prefix}-order-reports"
  tags        = local.common_tags
}

module "s3_inventory_reports" {
  source = "../modules/s3-reports-bucket"

  bucket_name = "${local.name_prefix}-inventory-reports"
  tags        = local.common_tags
}

# SQS Queue for Report Events (shared across environments)
module "sqs_reports_queue" {
  source = "../modules/sqs-queue"

  queue_name = "${local.name_prefix}-reports-queue"
  tags       = local.common_tags
}
```

#### Step 1.3: Update infrastructure/common/outputs.tf
Add outputs for S3 and SQS:
```terraform
output "s3_order_reports_bucket_name" {
  value = module.s3_order_reports.bucket_name
}

output "s3_inventory_reports_bucket_name" {
  value = module.s3_inventory_reports.bucket_name
}

output "sqs_reports_queue_url" {
  value = module.sqs_reports_queue.queue_url
}
```

#### Step 1.4: Update infrastructure/production/main.tf
Add environment variables to service configs:
```terraform
# In locals.service_env_vars:
inventory = {
  DATABASE_URL          = "postgresql://..."
  S3_REPORTS_BUCKET     = data.terraform_remote_state.common.outputs.s3_inventory_reports_bucket_name
  SQS_REPORTS_QUEUE_URL = data.terraform_remote_state.common.outputs.sqs_reports_queue_url
  AWS_REGION            = var.aws_region
}

order = {
  DATABASE_URL          = "postgresql://..."
  S3_REPORTS_BUCKET     = data.terraform_remote_state.common.outputs.s3_order_reports_bucket_name
  SQS_REPORTS_QUEUE_URL = data.terraform_remote_state.common.outputs.sqs_reports_queue_url
  AWS_REGION            = var.aws_region
}

bff = {
  # ... existing vars ...
  SQS_REPORTS_QUEUE_URL = data.terraform_remote_state.common.outputs.sqs_reports_queue_url
}
```

#### Step 1.5: Remove Problematic Cognito Client IDs
In `infrastructure/production/main.tf`, **REMOVE** lines 44-46:
```terraform
# DELETE THESE LINES:
AWS_COGNITO_WEB_CLIENT_ID    = module.cognito.web_client_id
AWS_COGNITO_MOBILE_CLIENT_ID = module.cognito.mobile_client_id
```

Reason: BFF handles auth directly, no hosted UI needed.

---

### Phase 2: Code Integration

#### Step 2.1: SonarCloud Workflow
```bash
# Keep develop version - it has the coverage fixes
git checkout develop -- .github/workflows/sonarcloud.yml
```

#### Step 2.2: Order Microservice Reports
```bash
# Add reports functionality to order
git checkout martin/reports -- order/src/adapters/input/controllers/reports_controller.py
git checkout martin/reports -- order/src/adapters/input/schemas/report_schemas.py
git checkout martin/reports -- order/src/infrastructure/database/models/report.py
git checkout martin/reports -- order/alembic/versions/a5d4684abb15_*.py

# Manually merge order/app.py to register reports router
# Add to order/app.py:
from src.adapters.input.controllers import reports_controller
app.include_router(reports_controller.router, prefix="/order", tags=["order"])
```

#### Step 2.3: Inventory Microservice Reports
```bash
# Add reports functionality to inventory
git checkout martin/reports -- inventory/src/infrastructure/database/models/report.py
git checkout martin/reports -- inventory/alembic/versions/04c5aec22c99_*.py

# Update inventory/src/infrastructure/database/models/__init__.py
# Manually add: from .report import Report
```

#### Step 2.4: BFF Reports Integration
```bash
# Add BFF reports endpoints
git checkout martin/reports -- bff/web/adapters/reports_adapter.py
git checkout martin/reports -- bff/web/controllers/reports_controller.py
git checkout martin/reports -- bff/tests/web/adapters/test_reports_adapter.py
git checkout martin/reports -- bff/tests/web/controllers/test_reports_controller.py

# Manually merge bff/app.py to include reports router
# Manually merge bff/web/router.py to add reports routes
```

---

### Phase 3: Local Testing & Validation

#### Step 3.1: Test Database Migrations Locally
```bash
# Start local PostgreSQL containers
docker-compose up -d order-db inventory-db

# Test Order migrations
cd order
alembic upgrade head  # Creates reports table
alembic history      # Verify migration chain
psql postgresql://postgres:postgres@localhost:5436/orderdb2 \
  -c "\dt" \
  -c "\d reports"  # Verify table structure

# Test Inventory migrations
cd ../inventory
alembic upgrade head  # Creates reports table
alembic history
psql postgresql://postgres:postgres@localhost:5437/inventory2 \
  -c "\dt" \
  -c "\d reports"  # Verify table structure

# Verify no foreign key or constraint conflicts
```

#### Step 3.2: Run All Tests Locally
```bash
# Build and start all services locally with docker-compose
docker-compose down
docker-compose build
docker-compose up -d

# Wait for services to be healthy
sleep 10

# Test each microservice
cd order && poetry run pytest --cov=src --cov-report=xml --cov-report=term
cd ../inventory && poetry run pytest --cov=src --cov-report=xml --cov-report=term
cd ../bff && poetry run pytest --cov --cov-report=xml --cov-report=term

# Test reports endpoints manually
curl http://localhost:8004/order/health
curl -X POST http://localhost:8004/order/reports \
  -H "Content-Type: application/json" \
  -d '{"report_type":"sales","start_date":"2025-01-01","end_date":"2025-01-31"}'
```

#### Step 3.3: Verify Coverage Reports
```bash
# CRITICAL: Check current coverage baseline on develop
git checkout develop
cd order && poetry run pytest --cov=src --cov-report=term | grep "TOTAL"
cd ../inventory && poetry run pytest --cov=src --cov-report=term | grep "TOTAL"
cd ../bff && poetry run pytest --cov --cov-report=term | grep "TOTAL"

# Note these values - new coverage MUST be ≥ these values

# Switch back to integration branch
git checkout feature/reports-integration

# Verify coverage with reports code
cd order
poetry run pytest --cov=src --cov-report=xml:coverage.xml --cov-report=term
# Check that coverage % is ≥ baseline

grep 'filename=' coverage.xml | head -5
# Should show: filename="order/src/adapters/..."

cd ../inventory
poetry run pytest --cov=src --cov-report=xml:coverage.xml --cov-report=term
# Check that coverage % is ≥ baseline

grep 'filename=' coverage.xml | head -5
# Should show: filename="inventory/src/adapters/..."

cd ../bff
poetry run pytest --cov --cov-report=xml --cov-report=term
# Check that coverage % is ≥ baseline

# If coverage decreased, add tests for reports functionality!
```

#### Step 3.4: Test Reports Functionality End-to-End
```bash
# Verify reports workflow locally:
# 1. Create report request
# 2. Check report status
# 3. Verify S3 upload (using localstack if needed)
# 4. Check SQS message published

# Test with local AWS services (optional - localstack)
docker-compose -f docker-compose.localstack.yml up -d
aws --endpoint-url=http://localhost:4566 s3 ls
aws --endpoint-url=http://localhost:4566 sqs list-queues
```

---

### Phase 4: Staging Deployment

#### Step 4.1: Prepare Staging Environment
```bash
# Ensure staging EC2 instance is running
aws ec2 describe-instances \
  --filters "Name=tag:Environment,Values=staging" \
  --query 'Reservations[].Instances[].PublicIpAddress'

# SSH to staging instance
ssh -i ~/.ssh/stg-key.pem ec2-user@<STAGING_IP>
```

#### Step 4.2: Deploy Infrastructure to Staging
```bash
# Deploy common infrastructure (S3 + SQS)
cd infrastructure/common
terraform init
terraform plan
terraform apply -auto-approve

# Note the outputs - we'll need these
terraform output -json > common-outputs.json

# Update staging environment with outputs
cd ../staging
terraform init
terraform plan  # Should reference common S3/SQS outputs
terraform apply -auto-approve
```

#### Step 4.3: Update Staging Services
```bash
# On staging EC2 instance
cd /home/ec2-user/app

# Pull latest code
git fetch origin
git checkout feature/reports-integration
git pull

# Update .env files with new S3/SQS variables
# S3_REPORTS_BUCKET=medisupply-order-reports
# SQS_REPORTS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/.../medisupply-reports-queue

# Rebuild and restart services
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Monitor logs
docker-compose logs -f order inventory bff
```

#### Step 4.4: Run Migrations on Staging
```bash
# On staging EC2 - migrations run automatically in containers
# But verify they completed successfully

# Check Order migrations
docker-compose exec order alembic current
docker-compose exec order alembic history

# Check Inventory migrations
docker-compose exec inventory alembic current
docker-compose exec inventory alembic history

# Verify reports tables exist
docker-compose exec order-db psql -U postgres -d orderdb2 -c "\dt reports"
docker-compose exec inventory-db psql -U postgres -d inventory2 -c "\dt reports"
```

#### Step 4.5: Test Reports on Staging
```bash
# Test reports creation
STAGING_IP=<your-staging-ip>

# Health checks
curl http://$STAGING_IP:8004/order/health
curl http://$STAGING_IP:8005/inventory/health

# Create a test report
curl -X POST http://$STAGING_IP:8004/order/reports \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "sales",
    "start_date": "2025-01-01",
    "end_date": "2025-01-31"
  }?user_id=test-user-123'

# List reports
curl http://$STAGING_IP:8004/order/reports?user_id=test-user-123

# Verify S3 bucket has files
aws s3 ls s3://medisupply-order-reports/

# Check SQS queue for messages
aws sqs get-queue-attributes \
  --queue-url $(terraform -chdir=infrastructure/common output -raw sqs_reports_queue_url) \
  --attribute-names ApproximateNumberOfMessages
```

---

## Conflict Resolution Checklist

- [ ] Infrastructure modules (s3-reports-bucket, sqs-queue) copied
- [ ] infrastructure/common/main.tf updated with S3 + SQS
- [ ] infrastructure/common/outputs.tf updated
- [ ] infrastructure/production/main.tf updated with env vars
- [ ] Cognito client IDs removed from production/main.tf
- [ ] .github/workflows/sonarcloud.yml conflicts resolved (keep develop)
- [ ] order/app.py merged (add reports router)
- [ ] order reports functionality integrated
- [ ] inventory reports functionality integrated
- [ ] BFF reports endpoints integrated
- [ ] All tests passing
- [ ] Coverage reports generating correctly
- [ ] Terraform plans successful
- [ ] Database migrations created and tested

---

## Risk Assessment

### High Risk Areas

1. **Test coverage regression**: Reports code may lower overall coverage percentage
   - **RULE**: Coverage must NOT decrease from current develop baseline
   - Reports functionality must have comprehensive tests
   - Check coverage before and after merge
2. **Infrastructure state conflicts**: Terraform state may need manual intervention if resources already exist
3. **Database migrations**: Reports tables must not conflict with existing schemas
4. **Environment variable mismatches**: Services expect S3/SQS vars but infra not deployed

### Mitigation Strategies

1. **Coverage**: Measure baseline before merge, add tests for reports if coverage drops, gate merge on coverage maintenance
2. **Infrastructure**: Deploy common infra first, verify outputs before updating staging
3. **Database**: Test migrations locally with docker-compose, verify on staging before production
4. **Environment**: Update .env.example files, document required new variables

### Rollback Plan

If merge fails:
```bash
git merge --abort
git checkout develop
git branch -D feature/reports-integration
```

If deployed but broken:
```bash
# Revert infrastructure
cd infrastructure/common
terraform destroy -target=module.s3_order_reports
terraform destroy -target=module.s3_inventory_reports
terraform destroy -target=module.sqs_reports_queue

# Rollback code
git revert <merge-commit-sha>
```

---

## Timeline Estimate

- **Phase 1** (Infrastructure): 2-3 hours
- **Phase 2** (Code Integration): 3-4 hours
- **Phase 3** (Local Testing & Migrations): 3-4 hours
  - Test migrations locally with docker-compose
  - Verify all table relationships
  - End-to-end reports testing
- **Phase 4** (Staging Deployment): 2-3 hours
  - Deploy common infrastructure (S3 + SQS)
  - Update staging EC2 with new code
  - Verify migrations on staging databases
  - Test reports functionality on staging

**Total**: 10-14 hours of focused work

**Note**: No direct RDS migrations needed. Everything tested locally first, then deployed to staging EC2 where migrations run automatically in containers.

---

## Success Criteria

- [ ] All tests passing in integration branch
- [ ] **CRITICAL**: Test coverage ≥ current levels (cannot decrease)
  - Check current coverage on develop before merge
  - Ensure reports code has adequate test coverage
  - All new code must be tested
  - SonarCloud quality gate must pass
- [ ] SonarCloud coverage reports showing correct percentages (paths fixed)
- [ ] Infrastructure deploys successfully (S3 + SQS created)
- [ ] Reports endpoints functional in Order and Inventory services
- [ ] BFF can proxy reports requests correctly
- [ ] Database migrations tested locally and applied without errors on staging
- [ ] No regression in existing functionality
- [ ] Code review approved by team
- [ ] Staging deployment successful and verified

---

## Notes

- The infrastructure restructuring in `develop` (common/staging/production split) is superior to the monolithic approach in `martin/reports`
- Reports functionality is self-contained and should integrate cleanly once infrastructure conflicts are resolved
- SonarCloud fixes in `develop` must be preserved - they solve the 0% coverage issue
- Cognito client IDs removal is critical - BFF handles auth directly without hosted UI

---

## Next Steps

1. Create `feature/reports-integration` branch
2. Attempt merge and identify actual conflicts
3. Work through resolution phases systematically
4. Test thoroughly at each phase
5. Get team review before merging to develop
6. Deploy to staging for final validation
7. Merge to develop
8. Deploy to production

---

**Document Version**: 1.0
**Created**: 2025-10-26
**Author**: Claude Code Analysis

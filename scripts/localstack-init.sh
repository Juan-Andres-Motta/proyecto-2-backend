#!/bin/bash
# LocalStack initialization script for CI/CD environment
# This script runs automatically when LocalStack becomes ready
# It sets up: Cognito User Pool, SQS Queue, S3 Bucket

set -e

echo "🚀 Starting LocalStack initialization for CI environment..."

# Configuration
REGION="us-east-1"
POOL_ID="us-east-1_cipool"
POOL_NAME="MediSupply-CI"
WEB_CLIENT_ID="ciwebclient"
MOBILE_CLIENT_ID="cimobileclient"
REPORTS_QUEUE_NAME="reports-queue"
REPORTS_BUCKET_NAME="reports-bucket"

# LocalStack endpoint (internal docker network)
ENDPOINT="http://localhost:4566"

# ==========================================
# 1. Setup Cognito User Pool
# ==========================================
echo "📝 Setting up Cognito User Pool..."

# Create User Pool with custom ID
awslocal cognito-idp create-user-pool \
  --pool-name "$POOL_NAME" \
  --region "$REGION" \
  --policies '{
    "PasswordPolicy": {
      "MinimumLength": 8,
      "RequireUppercase": true,
      "RequireLowercase": true,
      "RequireNumbers": true,
      "RequireSymbols": false
    }
  }' \
  --auto-verified-attributes email \
  --tags "_custom_id_=cipool" \
  --no-cli-pager > /dev/null 2>&1 || echo "  ⚠️  User pool might already exist"

echo "✅ User pool created/verified: $POOL_ID"

# Create Web Client
awslocal cognito-idp create-user-pool-client \
  --user-pool-id "$POOL_ID" \
  --client-name "web-client" \
  --region "$REGION" \
  --explicit-auth-flows ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH \
  --no-cli-pager > /dev/null 2>&1 || echo "  ⚠️  Web client might already exist"

echo "✅ Web client created: $WEB_CLIENT_ID"

# Create Mobile Client
awslocal cognito-idp create-user-pool-client \
  --user-pool-id "$POOL_ID" \
  --client-name "mobile-client" \
  --region "$REGION" \
  --explicit-auth-flows ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH \
  --no-cli-pager > /dev/null 2>&1 || echo "  ⚠️  Mobile client might already exist"

echo "✅ Mobile client created: $MOBILE_CLIENT_ID"

# Create Cognito Groups
echo "👥 Creating Cognito groups..."

awslocal cognito-idp create-group \
  --group-name "web_users" \
  --user-pool-id "$POOL_ID" \
  --description "Web application users" \
  --region "$REGION" \
  --no-cli-pager > /dev/null 2>&1 || true

awslocal cognito-idp create-group \
  --group-name "mobile_users" \
  --user-pool-id "$POOL_ID" \
  --description "Mobile application users" \
  --region "$REGION" \
  --no-cli-pager > /dev/null 2>&1 || true

awslocal cognito-idp create-group \
  --group-name "sellers" \
  --user-pool-id "$POOL_ID" \
  --description "Seller users" \
  --region "$REGION" \
  --no-cli-pager > /dev/null 2>&1 || true

echo "✅ Groups created: web_users, mobile_users, sellers"

# Create Test Users
echo "👤 Creating test users for CI..."

# Test web user
awslocal cognito-idp admin-create-user \
  --user-pool-id "$POOL_ID" \
  --username "testwebuser" \
  --user-attributes \
    Name=email,Value=testwebuser@example.com \
    Name=email_verified,Value=true \
    Name=name,Value="Test Web User" \
    Name=custom:user_type,Value=client \
  --message-action SUPPRESS \
  --region "$REGION" \
  --no-cli-pager > /dev/null 2>&1 || true

awslocal cognito-idp admin-set-user-password \
  --user-pool-id "$POOL_ID" \
  --username "testwebuser" \
  --password "TestPass123!" \
  --permanent \
  --region "$REGION" \
  --no-cli-pager > /dev/null 2>&1 || true

awslocal cognito-idp admin-add-user-to-group \
  --user-pool-id "$POOL_ID" \
  --username "testwebuser" \
  --group-name "web_users" \
  --region "$REGION" \
  --no-cli-pager > /dev/null 2>&1 || true

echo "✅ Test user: testwebuser@example.com / TestPass123!"

# Test seller
awslocal cognito-idp admin-create-user \
  --user-pool-id "$POOL_ID" \
  --username "testseller" \
  --user-attributes \
    Name=email,Value=testseller@example.com \
    Name=email_verified,Value=true \
    Name=name,Value="Test Seller" \
    Name=custom:user_type,Value=seller \
  --message-action SUPPRESS \
  --region "$REGION" \
  --no-cli-pager > /dev/null 2>&1 || true

awslocal cognito-idp admin-set-user-password \
  --user-pool-id "$POOL_ID" \
  --username "testseller" \
  --password "SellerPass123!" \
  --permanent \
  --region "$REGION" \
  --no-cli-pager > /dev/null 2>&1 || true

awslocal cognito-idp admin-add-user-to-group \
  --user-pool-id "$POOL_ID" \
  --username "testseller" \
  --group-name "sellers" \
  --region "$REGION" \
  --no-cli-pager > /dev/null 2>&1 || true

echo "✅ Test seller: testseller@example.com / SellerPass123!"

# ==========================================
# 2. Setup SQS Queue
# ==========================================
echo "📬 Setting up SQS queue..."

awslocal sqs create-queue \
  --queue-name "$REPORTS_QUEUE_NAME" \
  --region "$REGION" \
  --attributes '{
    "VisibilityTimeout": "30",
    "MessageRetentionPeriod": "345600",
    "DelaySeconds": "0"
  }' \
  --no-cli-pager > /dev/null 2>&1 || echo "  ⚠️  Queue might already exist"

echo "✅ SQS queue created: $REPORTS_QUEUE_NAME"
echo "   Queue URL: http://localhost:4566/000000000000/$REPORTS_QUEUE_NAME"

# ==========================================
# 3. Setup S3 Bucket
# ==========================================
echo "🪣 Setting up S3 bucket..."

awslocal s3 mb "s3://$REPORTS_BUCKET_NAME" \
  --region "$REGION" 2>&1 | grep -v "BucketAlreadyOwnedByYou" || true

# Enable versioning (optional)
awslocal s3api put-bucket-versioning \
  --bucket "$REPORTS_BUCKET_NAME" \
  --versioning-configuration Status=Enabled \
  --region "$REGION" > /dev/null 2>&1 || true

echo "✅ S3 bucket created: $REPORTS_BUCKET_NAME"

# ==========================================
# 4. Verification
# ==========================================
echo ""
echo "🔍 Verifying setup..."

# Check Cognito
JWKS_URL="$ENDPOINT/$POOL_ID/.well-known/jwks.json"
if curl -s "$JWKS_URL" | grep -q "keys"; then
  echo "✅ Cognito JWKS endpoint responding: $JWKS_URL"
else
  echo "❌ Cognito JWKS endpoint not responding"
fi

# Check SQS
QUEUE_COUNT=$(awslocal sqs list-queues --region "$REGION" 2>/dev/null | grep -c "$REPORTS_QUEUE_NAME" || echo "0")
if [ "$QUEUE_COUNT" -gt 0 ]; then
  echo "✅ SQS queue verified"
else
  echo "❌ SQS queue not found"
fi

# Check S3
BUCKET_COUNT=$(awslocal s3 ls 2>/dev/null | grep -c "$REPORTS_BUCKET_NAME" || echo "0")
if [ "$BUCKET_COUNT" -gt 0 ]; then
  echo "✅ S3 bucket verified"
else
  echo "❌ S3 bucket not found"
fi

# ==========================================
# Summary
# ==========================================
echo ""
echo "🎉 LocalStack initialization complete!"
echo ""
echo "📋 Configuration Summary:"
echo "   Environment: CI/CD"
echo "   Region: $REGION"
echo ""
echo "   🔐 Cognito:"
echo "      User Pool ID: $POOL_ID"
echo "      Web Client ID: $WEB_CLIENT_ID"
echo "      Mobile Client ID: $MOBILE_CLIENT_ID"
echo "      JWKS URL: $JWKS_URL"
echo ""
echo "   📬 SQS:"
echo "      Queue Name: $REPORTS_QUEUE_NAME"
echo "      Queue URL: http://localhost:4566/000000000000/$REPORTS_QUEUE_NAME"
echo ""
echo "   🪣 S3:"
echo "      Bucket Name: $REPORTS_BUCKET_NAME"
echo ""
echo "   👥 Test Accounts:"
echo "      Web User: testwebuser@example.com / TestPass123!"
echo "      Seller: testseller@example.com / SellerPass123!"
echo ""
echo "✨ Ready for integration tests!"

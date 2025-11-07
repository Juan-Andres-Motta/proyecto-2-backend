#!/bin/bash
# LocalStack initialization script for CI/CD environment
# This script runs automatically when LocalStack becomes ready
# It sets up: SQS Queue, S3 Bucket
# Note: Using real AWS Cognito (not LocalStack) - Auth is mocked in TEST_MODE

set -e  # Exit on error
set -x  # Print commands for debugging

echo "🚀 Starting LocalStack initialization for CI environment..."

# Configuration
REGION="us-east-1"
REPORTS_QUEUE_NAME="reports-queue"
REPORTS_BUCKET_NAME="reports-bucket"

# Wait a bit for LocalStack to be fully ready
echo "⏳ Waiting for LocalStack to be fully ready..."
sleep 5

# ==========================================
# 1. Setup SQS Queue
# ==========================================
echo "📬 Setting up SQS queue..."

# Create SQS queue
awslocal sqs create-queue \
  --queue-name "$REPORTS_QUEUE_NAME" \
  --region "$REGION" \
  --attributes VisibilityTimeout=30,MessageRetentionPeriod=345600,DelaySeconds=0 \
  || echo "⚠️  Queue creation failed or already exists"

echo "✅ SQS queue created/verified: $REPORTS_QUEUE_NAME"

# ==========================================
# 2. Setup S3 Bucket
# ==========================================
echo "🪣 Setting up S3 bucket..."

# Create S3 bucket
awslocal s3 mb "s3://$REPORTS_BUCKET_NAME" --region "$REGION" \
  || echo "⚠️  Bucket creation failed or already exists"

echo "✅ S3 bucket created/verified: $REPORTS_BUCKET_NAME"

# ==========================================
# 3. Verification
# ==========================================
echo ""
echo "🔍 Verifying LocalStack resources..."

# List and verify SQS queues
echo "📋 SQS Queues:"
awslocal sqs list-queues --region "$REGION" || echo "No queues found or error listing"

# List and verify S3 buckets
echo "📋 S3 Buckets:"
awslocal s3 ls || echo "No buckets found or error listing"

# Final check
QUEUE_URL=$(awslocal sqs list-queues --region "$REGION" 2>/dev/null | grep "$REPORTS_QUEUE_NAME" || echo "")
BUCKET_FOUND=$(awslocal s3 ls 2>/dev/null | grep "$REPORTS_BUCKET_NAME" || echo "")

if [ -n "$QUEUE_URL" ]; then
  echo "✅ SQS queue verified: $REPORTS_QUEUE_NAME"
else
  echo "❌ SQS queue not found: $REPORTS_QUEUE_NAME"
  echo "   This may cause integration tests to fail"
fi

if [ -n "$BUCKET_FOUND" ]; then
  echo "✅ S3 bucket verified: $REPORTS_BUCKET_NAME"
else
  echo "❌ S3 bucket not found: $REPORTS_BUCKET_NAME"
  echo "   This may cause integration tests to fail"
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
echo "   Queue Name: $REPORTS_QUEUE_NAME"
echo "   Bucket Name: $REPORTS_BUCKET_NAME"
echo "   🔐 Authentication: Using real AWS Cognito (not LocalStack)"
echo ""
echo "✨ Ready for integration tests!"

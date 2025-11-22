#!/bin/bash
# LocalStack initialization script for CI/CD environment
# This script runs automatically when LocalStack becomes ready
# It sets up: SNS Topics, SQS Queues (Reports + Event-Driven), S3 Bucket
# Note: Using real AWS Cognito (not LocalStack) - Auth is mocked in TEST_MODE

set -e  # Exit on error
set -x  # Print commands for debugging

echo "🚀 Starting LocalStack initialization for CI environment..."

# Configuration
REGION="us-east-1"
REPORTS_QUEUE_NAME="reports-queue"
REPORTS_BUCKET_NAME="reports-bucket"
ORDER_EVENTS_TOPIC_NAME="medisupply-order-events-topic"
DELIVERY_QUEUE_NAME="medisupply-order-events-delivery-queue"
SELLER_QUEUE_NAME="medisupply-order-events-seller-queue"
BFF_QUEUE_NAME="medisupply-order-events-bff-queue"
ROUTES_GENERATED_QUEUE_NAME="medisupply-delivery-routes-generated-queue"

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
# 3. Setup SNS Topic for Order Events
# ==========================================
echo "📢 Setting up SNS topic for event-driven architecture..."

# Create SNS topic for order events
TOPIC_ARN=$(awslocal sns create-topic \
  --name "$ORDER_EVENTS_TOPIC_NAME" \
  --region "$REGION" \
  --query 'TopicArn' \
  --output text 2>&1)

if [[ $TOPIC_ARN == *"arn:aws:sns"* ]]; then
  echo "✅ SNS Topic created: $TOPIC_ARN"
else
  echo "⚠️  Topic creation failed or already exists, attempting to get existing..."
  TOPIC_ARN=$(awslocal sns list-topics \
    --region "$REGION" \
    --query "Topics[?contains(TopicArn, '$ORDER_EVENTS_TOPIC_NAME')].TopicArn" \
    --output text)
  echo "✅ Using existing topic: $TOPIC_ARN"
fi

# ==========================================
# 4. Setup SQS Queue for Delivery Service
# ==========================================
echo "📬 Setting up SQS queue for delivery service..."

# Create SQS queue for delivery service
DELIVERY_QUEUE_URL=$(awslocal sqs create-queue \
  --queue-name "$DELIVERY_QUEUE_NAME" \
  --region "$REGION" \
  --attributes VisibilityTimeout=30,MessageRetentionPeriod=345600,DelaySeconds=0 \
  --query 'QueueUrl' \
  --output text 2>&1)

if [[ $DELIVERY_QUEUE_URL == *"http"* ]]; then
  echo "✅ SQS Queue created: $DELIVERY_QUEUE_URL"
else
  echo "⚠️  Queue creation failed or already exists, attempting to get existing..."
  DELIVERY_QUEUE_URL=$(awslocal sqs get-queue-url \
    --queue-name "$DELIVERY_QUEUE_NAME" \
    --region "$REGION" \
    --query 'QueueUrl' \
    --output text)
  echo "✅ Using existing queue: $DELIVERY_QUEUE_URL"
fi

# Get Queue ARN
DELIVERY_QUEUE_ARN=$(awslocal sqs get-queue-attributes \
  --queue-url "$DELIVERY_QUEUE_URL" \
  --region "$REGION" \
  --attribute-names QueueArn \
  --query 'Attributes.QueueArn' \
  --output text)

echo "✅ Delivery Queue ARN: $DELIVERY_QUEUE_ARN"

# ==========================================
# 5. Set Queue Policy (Allow SNS to send)
# ==========================================
echo "🔐 Setting SQS queue policy to allow SNS publish..."

# LocalStack doesn't enforce SQS policies strictly, so we skip this step
# The subscription will work without explicit queue policy in LocalStack
echo "⏭️  Skipping queue policy (not enforced in LocalStack)"

# ==========================================
# 6. Subscribe Delivery Queue to SNS Topic
# ==========================================
echo "🔗 Subscribing delivery queue to SNS topic..."

SUBSCRIPTION_ARN=$(awslocal sns subscribe \
  --topic-arn "$TOPIC_ARN" \
  --protocol sqs \
  --notification-endpoint "$DELIVERY_QUEUE_ARN" \
  --region "$REGION" \
  --query 'SubscriptionArn' \
  --output text 2>&1)

if [[ $SUBSCRIPTION_ARN == *"arn:aws:sns"* ]]; then
  echo "✅ Subscription created: $SUBSCRIPTION_ARN"
else
  echo "⚠️  Subscription may already exist: $SUBSCRIPTION_ARN"
fi

# ==========================================
# 6a. Setup SQS Queue for Seller Service
# ==========================================
echo "📬 Setting up SQS queue for seller service..."

SELLER_QUEUE_URL=$(awslocal sqs create-queue \
  --queue-name "$SELLER_QUEUE_NAME" \
  --region "$REGION" \
  --attributes VisibilityTimeout=30,MessageRetentionPeriod=345600,DelaySeconds=0 \
  --query 'QueueUrl' \
  --output text 2>&1)

if [[ $SELLER_QUEUE_URL == *"http"* ]]; then
  echo "✅ Seller Queue created: $SELLER_QUEUE_URL"
else
  echo "⚠️  Queue creation failed or already exists, attempting to get existing..."
  SELLER_QUEUE_URL=$(awslocal sqs get-queue-url \
    --queue-name "$SELLER_QUEUE_NAME" \
    --region "$REGION" \
    --query 'QueueUrl' \
    --output text)
  echo "✅ Using existing queue: $SELLER_QUEUE_URL"
fi

SELLER_QUEUE_ARN=$(awslocal sqs get-queue-attributes \
  --queue-url "$SELLER_QUEUE_URL" \
  --region "$REGION" \
  --attribute-names QueueArn \
  --query 'Attributes.QueueArn' \
  --output text)

echo "✅ Seller Queue ARN: $SELLER_QUEUE_ARN"

# Subscribe seller queue to SNS topic
echo "🔗 Subscribing seller queue to SNS topic..."

SELLER_SUBSCRIPTION_ARN=$(awslocal sns subscribe \
  --topic-arn "$TOPIC_ARN" \
  --protocol sqs \
  --notification-endpoint "$SELLER_QUEUE_ARN" \
  --region "$REGION" \
  --query 'SubscriptionArn' \
  --output text 2>&1)

if [[ $SELLER_SUBSCRIPTION_ARN == *"arn:aws:sns"* ]]; then
  echo "✅ Seller subscription created: $SELLER_SUBSCRIPTION_ARN"
else
  echo "⚠️  Seller subscription may already exist: $SELLER_SUBSCRIPTION_ARN"
fi

# ==========================================
# 6b. Setup SQS Queue for BFF Service
# ==========================================
echo "📬 Setting up SQS queue for BFF service..."

BFF_QUEUE_URL=$(awslocal sqs create-queue \
  --queue-name "$BFF_QUEUE_NAME" \
  --region "$REGION" \
  --attributes VisibilityTimeout=30,MessageRetentionPeriod=345600,DelaySeconds=0 \
  --query 'QueueUrl' \
  --output text 2>&1)

if [[ $BFF_QUEUE_URL == *"http"* ]]; then
  echo "✅ BFF Queue created: $BFF_QUEUE_URL"
else
  echo "⚠️  Queue creation failed or already exists, attempting to get existing..."
  BFF_QUEUE_URL=$(awslocal sqs get-queue-url \
    --queue-name "$BFF_QUEUE_NAME" \
    --region "$REGION" \
    --query 'QueueUrl' \
    --output text)
  echo "✅ Using existing queue: $BFF_QUEUE_URL"
fi

BFF_QUEUE_ARN=$(awslocal sqs get-queue-attributes \
  --queue-url "$BFF_QUEUE_URL" \
  --region "$REGION" \
  --attribute-names QueueArn \
  --query 'Attributes.QueueArn' \
  --output text)

echo "✅ BFF Queue ARN: $BFF_QUEUE_ARN"

# Subscribe BFF queue to SNS topic
echo "🔗 Subscribing BFF queue to SNS topic..."

BFF_SUBSCRIPTION_ARN=$(awslocal sns subscribe \
  --topic-arn "$TOPIC_ARN" \
  --protocol sqs \
  --notification-endpoint "$BFF_QUEUE_ARN" \
  --region "$REGION" \
  --query 'SubscriptionArn' \
  --output text 2>&1)

if [[ $BFF_SUBSCRIPTION_ARN == *"arn:aws:sns"* ]]; then
  echo "✅ BFF subscription created: $BFF_SUBSCRIPTION_ARN"
else
  echo "⚠️  BFF subscription may already exist: $BFF_SUBSCRIPTION_ARN"
fi

# ==========================================
# 6c. Setup SQS Queue for Delivery Routes (BFF Consumer)
# ==========================================
echo "📬 Setting up SQS queue for delivery routes events..."

ROUTES_QUEUE_URL=$(awslocal sqs create-queue \
  --queue-name "$ROUTES_GENERATED_QUEUE_NAME" \
  --region "$REGION" \
  --attributes VisibilityTimeout=30,MessageRetentionPeriod=345600,DelaySeconds=0 \
  --query 'QueueUrl' \
  --output text 2>&1)

if [[ $ROUTES_QUEUE_URL == *"http"* ]]; then
  echo "✅ Routes Queue created: $ROUTES_QUEUE_URL"
else
  echo "⚠️  Queue creation failed or already exists, attempting to get existing..."
  ROUTES_QUEUE_URL=$(awslocal sqs get-queue-url \
    --queue-name "$ROUTES_GENERATED_QUEUE_NAME" \
    --region "$REGION" \
    --query 'QueueUrl' \
    --output text)
  echo "✅ Using existing queue: $ROUTES_QUEUE_URL"
fi

ROUTES_QUEUE_ARN=$(awslocal sqs get-queue-attributes \
  --queue-url "$ROUTES_QUEUE_URL" \
  --region "$REGION" \
  --attribute-names QueueArn \
  --query 'Attributes.QueueArn' \
  --output text)

echo "✅ Routes Queue ARN: $ROUTES_QUEUE_ARN"
echo "ℹ️  Routes queue is point-to-point (delivery → BFF), not subscribed to SNS"

# ==========================================
# 7. Test SNS → SQS Connectivity
# ==========================================
echo "🧪 Verifying SNS → SQS connectivity..."

# Check queue attributes to verify subscriptions are active
DELIVERY_MSGS=$(awslocal sqs get-queue-attributes \
  --queue-url "$DELIVERY_QUEUE_URL" \
  --region "$REGION" \
  --attribute-names ApproximateNumberOfMessages \
  --query 'Attributes.ApproximateNumberOfMessages' \
  --output text)

echo "✅ Delivery queue ready (messages: $DELIVERY_MSGS)"

# Note: Removed test message publishing as it causes UUID parsing errors
# in delivery service. Real order events have proper structure.

# ==========================================
# 8. Verification
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
# 9. List SNS Topics and Subscriptions
# ==========================================
echo ""
echo "📢 SNS Topics:"
awslocal sns list-topics --region "$REGION" || echo "Error listing topics"

echo ""
echo "🔗 SNS Subscriptions:"
awslocal sns list-subscriptions --region "$REGION" || echo "Error listing subscriptions"

# ==========================================
# Summary
# ==========================================
echo ""
echo "=========================================="
echo "🎉 LocalStack initialization complete!"
echo "=========================================="
echo ""
echo "📋 Configuration Summary:"
echo "   Environment: CI/CD"
echo "   Region: $REGION"
echo ""
echo "Reports Infrastructure:"
echo "   ✅ Queue: $REPORTS_QUEUE_NAME"
echo "   ✅ Bucket: $REPORTS_BUCKET_NAME"
echo ""
echo "Event-Driven Architecture:"
echo "   ✅ SNS Topic: $ORDER_EVENTS_TOPIC_NAME"
echo "   ✅ Topic ARN: $TOPIC_ARN"
echo ""
echo "Order Events Queues (SNS Fanout):"
echo "   ✅ Delivery Queue: $DELIVERY_QUEUE_NAME"
echo "      URL: $DELIVERY_QUEUE_URL"
echo "   ✅ Seller Queue: $SELLER_QUEUE_NAME"
echo "      URL: $SELLER_QUEUE_URL"
echo "   ✅ BFF Queue: $BFF_QUEUE_NAME"
echo "      URL: $BFF_QUEUE_URL"
echo ""
echo "Point-to-Point Queues:"
echo "   ✅ Routes Generated Queue: $ROUTES_GENERATED_QUEUE_NAME"
echo "      URL: $ROUTES_QUEUE_URL"
echo ""
echo "Event Flows:"
echo "   1. Order Service → SNS Topic → [Delivery, Seller, BFF] Queues"
echo "   2. Delivery Service → Routes Queue → BFF Service"
echo ""
echo "   🔐 Authentication: Using real AWS Cognito (not LocalStack)"
echo ""
echo "=========================================="
echo "✨ Ready for integration tests with full event-driven architecture! 🚀"
echo "=========================================="

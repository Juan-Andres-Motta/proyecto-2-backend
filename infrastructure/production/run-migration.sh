#!/bin/bash

# Script to run database migrations for any microservice
# Usage: ./run-migration.sh <service-name>

set -e

SERVICE_NAME=$1
CLUSTER="medisupply-cluster"
REGION="us-east-1"

if [ -z "$SERVICE_NAME" ]; then
    echo "Usage: $0 <service-name>"
    echo "Example: $0 catalog"
    echo ""
    echo "Available services: catalog, client, delivery, inventory, order, seller"
    exit 1
fi

echo "🚀 Running migration for $SERVICE_NAME service..."

# Get the ECS service name
ECS_SERVICE="${CLUSTER%-cluster}-${SERVICE_NAME}-service"

# Get network configuration from the service
echo "📡 Getting network configuration..."
NETWORK_CONFIG=$(aws ecs describe-services \
    --cluster "$CLUSTER" \
    --services "$ECS_SERVICE" \
    --region "$REGION" \
    --query 'services[0].networkConfiguration.awsvpcConfiguration' \
    --output json)

if [ "$NETWORK_CONFIG" == "null" ]; then
    echo "❌ Error: Could not find service $ECS_SERVICE"
    exit 1
fi

SUBNETS=$(echo "$NETWORK_CONFIG" | jq -r '.subnets | join(",")')
SECURITY_GROUPS=$(echo "$NETWORK_CONFIG" | jq -r '.securityGroups | join(",")')

echo "  Subnets: $SUBNETS"
echo "  Security Groups: $SECURITY_GROUPS"

# Get the latest task definition
echo "🔍 Getting latest task definition..."
TASK_DEF=$(aws ecs describe-services \
    --cluster "$CLUSTER" \
    --services "$ECS_SERVICE" \
    --region "$REGION" \
    --query 'services[0].taskDefinition' \
    --output text)

echo "  Task Definition: $TASK_DEF"

# Run the migration task
echo "▶️  Starting migration task..."
TASK_ARN=$(aws ecs run-task \
    --cluster "$CLUSTER" \
    --task-definition "$TASK_DEF" \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[$SUBNETS],securityGroups=[$SECURITY_GROUPS],assignPublicIp=ENABLED}" \
    --overrides "{\"containerOverrides\":[{\"name\":\"$SERVICE_NAME\",\"command\":[\"sh\",\"-c\",\"poetry run alembic upgrade head\"]}]}" \
    --region "$REGION" \
    --query 'tasks[0].taskArn' \
    --output text)

echo "  Task ARN: $TASK_ARN"
TASK_ID=$(echo "$TASK_ARN" | awk -F'/' '{print $NF}')

# Wait for task to complete
echo "⏳ Waiting for migration to complete..."
MAX_WAIT=120
WAITED=0

while [ $WAITED -lt $MAX_WAIT ]; do
    TASK_STATUS=$(aws ecs describe-tasks \
        --cluster "$CLUSTER" \
        --tasks "$TASK_ARN" \
        --region "$REGION" \
        --query 'tasks[0].lastStatus' \
        --output text)

    if [ "$TASK_STATUS" == "STOPPED" ] || [ "$TASK_STATUS" == "DEPROVISIONING" ]; then
        break
    fi

    echo "  Status: $TASK_STATUS"
    sleep 5
    WAITED=$((WAITED + 5))
done

# Get exit code and logs
EXIT_CODE=$(aws ecs describe-tasks \
    --cluster "$CLUSTER" \
    --tasks "$TASK_ARN" \
    --region "$REGION" \
    --query 'tasks[0].containers[0].exitCode' \
    --output text)

echo ""
echo "📋 Migration logs:"
echo "----------------------------------------"
aws logs tail "/ecs/medisupply/$SERVICE_NAME" \
    --since 5m \
    --region "$REGION" \
    --filter-pattern "alembic" 2>/dev/null || echo "No logs available yet"

echo "----------------------------------------"
echo ""

if [ "$EXIT_CODE" == "0" ]; then
    echo "✅ Migration completed successfully!"
    exit 0
else
    echo "❌ Migration failed with exit code: $EXIT_CODE"
    exit 1
fi

#!/bin/bash
# Helper script to run integration tests in CI mode locally
# This simulates the CI/CD environment on your local machine

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting CI Integration Test Environment${NC}"
echo ""

# Change to project root
cd "$(dirname "$0")/.."

# Check if docker-compose.ci.yml exists
if [ ! -f "docker-compose.ci.yml" ]; then
    echo -e "${RED}❌ docker-compose.ci.yml not found${NC}"
    exit 1
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}🧹 Cleaning up...${NC}"
    docker-compose -f docker-compose.ci.yml down -v 2>/dev/null || true
}

# Register cleanup function
trap cleanup EXIT INT TERM

# Build and start services
echo -e "${GREEN}🏗️  Building and starting services...${NC}"
docker-compose -f docker-compose.ci.yml up -d --build

# Wait for LocalStack to be healthy
echo ""
echo -e "${YELLOW}⏳ Waiting for LocalStack to be ready...${NC}"
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if docker-compose -f docker-compose.ci.yml ps localstack | grep -q "healthy"; then
        echo -e "${GREEN}✅ LocalStack is ready!${NC}"
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "   Attempt $RETRY_COUNT/$MAX_RETRIES..."
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}❌ LocalStack failed to become healthy${NC}"
    docker-compose -f docker-compose.ci.yml logs localstack
    exit 1
fi

# Wait a bit more for initialization to complete
echo ""
echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
sleep 10

# Check all services are up
echo ""
echo -e "${GREEN}📊 Service Status:${NC}"
docker-compose -f docker-compose.ci.yml ps

# Verify LocalStack resources
echo ""
echo -e "${GREEN}🔍 Verifying LocalStack resources...${NC}"

# Check Cognito JWKS
if curl -sf http://localhost:4566/us-east-1_cipool/.well-known/jwks.json >/dev/null; then
    echo -e "${GREEN}✅ Cognito JWKS endpoint responding${NC}"
else
    echo -e "${RED}❌ Cognito JWKS endpoint not responding${NC}"
fi

# Check SQS Queue
if docker exec localstack awslocal sqs list-queues | grep -q "reports-queue"; then
    echo -e "${GREEN}✅ SQS queue available${NC}"
else
    echo -e "${RED}❌ SQS queue not found${NC}"
fi

# Check S3 Bucket
if docker exec localstack awslocal s3 ls | grep -q "reports-bucket"; then
    echo -e "${GREEN}✅ S3 bucket available${NC}"
else
    echo -e "${RED}❌ S3 bucket not found${NC}"
fi

# Run database migrations (if needed)
echo ""
echo -e "${GREEN}🗄️  Running database migrations...${NC}"
# Add your migration commands here if needed
# docker-compose -f docker-compose.ci.yml exec -T bff alembic upgrade head

# Run integration tests
echo ""
echo -e "${GREEN}🧪 Running integration tests...${NC}"
echo ""

if command -v newman &> /dev/null; then
    # Newman is installed, run tests
    newman run MediSupply_BFF_Complete.postman_collection.json \
        -e MediSupply_Local.postman_environment.json \
        --reporters cli,json \
        --reporter-json-export test-results-ci.json \
        --color on

    TEST_EXIT_CODE=$?

    if [ $TEST_EXIT_CODE -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✅ All tests passed!${NC}"
    else
        echo ""
        echo -e "${RED}❌ Some tests failed${NC}"
    fi

    exit $TEST_EXIT_CODE
else
    echo -e "${YELLOW}⚠️  Newman not installed. Install with: npm install -g newman${NC}"
    echo ""
    echo -e "${GREEN}Environment is ready for manual testing:${NC}"
    echo "   BFF: http://localhost:8000/bff/docs"
    echo "   LocalStack: http://localhost:4566"
    echo ""
    echo "Press Ctrl+C to stop services..."

    # Keep services running
    docker-compose -f docker-compose.ci.yml logs -f
fi

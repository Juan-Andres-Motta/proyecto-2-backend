# Microservices Project

This project consists of a set of microservices built with FastAPI and Python, orchestrated using Docker Compose. It includes a BFF (Backend for Frontend) service and 6 domain-specific services, each with its own PostgreSQL database.

## Services

### Microservices
- **BFF** (Backend for Frontend): Port 8000 - Entry point for client applications
- **Catalog**: Port 8001 - Manages product catalog
- **Client**: Port 8002 - Handles client/user management
- **Delivery**: Port 8003 - Manages delivery operations
- **Inventory**: Port 8004 - Tracks inventory levels
- **Order**: Port 8005 - Processes orders
- **Seller**: Port 8006 - Manages seller accounts

### Databases
Each service (except BFF) has its own PostgreSQL database:
- catalog-db: Port 5432
- client-db: Port 5433
- delivery-db: Port 5434
- inventory-db: Port 5435
- order-db: Port 5436
- seller-db: Port 5437

All services share a Docker network called `microservices` for inter-service communication.

## Prerequisites

- Docker
- Docker Compose

## Running the Application

### All Services + Databases
```bash
docker-compose up
```

### All Services + Databases + LocalStack for AWS Simulation
```bash
docker-compose -f docker-compose.local.yml up
```

### Individual Services

Each service directory contains Docker Compose files for running individually:

- `docker-compose.yml`: Runs only the service (assumes external database)
- `docker-compose.with-db.yml`: Runs the service with its own PostgreSQL database

Example for catalog service:
```bash
cd catalog
docker-compose up  # Service only
# or
docker-compose -f docker-compose.with-db.yml up  # Service + DB
```

LocalStack simulates S3 and SQS services locally. Access the web UI at `http://localhost:8007`.

## Environment Variables

Each service loads environment variables from its respective `.env` file:

- Database connections: `DATABASE_URL=postgresql://postgres:password@[service]-db:5432/[service]`
- For LocalStack: `AWS_ENDPOINT_URL=http://localstack:4566`

## Connecting to Databases

You can connect to each database from your local machine using any PostgreSQL client:

- Host: `localhost`
- Port: See database ports above
- User: `postgres`
- Password: `password`
- Database: Service name (e.g., `catalog`)

Example with psql:
```bash
psql -h localhost -p 5432 -U postgres -d catalog
```

## API Endpoints

Each service exposes a health check endpoint:
- `GET /health` - Returns service status

## Development

To add new features or modify services:
1. Edit the code in the respective service directory
2. Update the Dockerfile if dependencies change
3. Rebuild with `docker-compose build`

## Architecture

```
[Client] --> [BFF] --> [Catalog, Client, Delivery, Inventory, Order, Seller Services]
                    |         |
                    v         v
              [Databases]  [LocalStack (S3, SQS)]
```

All services communicate via the shared `microservices` network. The BFF acts as an API gateway for external clients.
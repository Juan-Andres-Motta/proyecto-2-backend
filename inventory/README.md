# Inventory Service

Inventory service built with FastAPI.

## Features

- Health check endpoint
- Root endpoint returning service name
- Store management (create and list stores)
- Inventory management (create and list inventory items)
- Database integration with PostgreSQL
- Alembic for database migrations
- Hexagonal architecture following clean code principles

## Installation

1. Ensure you have Python 3.13+ installed.
2. Install Poetry if not already installed: `curl -sSL https://install.python-poetry.org | python3 -`
3. Clone the repository and navigate to the project directory.
4. Install dependencies: `poetry install`
5. Copy `.env.example` to `.env` and configure environment variables

## Environment Variables

Create a `.env` file based on `.env.example`:

- `DATABASE_URL`: PostgreSQL connection string (default: `postgresql://postgres:password@inventory-db:5432/inventory`)
- `APP_NAME`: Application name (default: "Inventory Service")
- `LOG_LEVEL`: Logging level (default: "INFO")

## Running Locally

To run the service locally:

```
poetry run uvicorn main:app --reload
```

The service will be available at `http://localhost:8000`.

## Running with Docker

### Production

```
docker-compose up --build
```

### With Database

```
docker-compose -f docker-compose.with-db.yml up --build
```

### Tests

```
docker-compose -f docker-compose.test.yml up --build
```

## API Endpoints

### Common
- `GET /`: Returns service information
- `GET /health`: Health check endpoint

### Stores
- `POST /store`: Create a new store
- `GET /stores`: List stores with pagination (query params: limit, offset)

### Inventory
- `POST /inventory`: Create a new inventory item
- `GET /inventories`: List inventory items with pagination (query params: limit, offset)

## Database Setup

1. Ensure PostgreSQL is running
2. Run database migrations: `alembic upgrade head`
3. The service will create and manage the following tables:
   - `stores`: Store information
   - `inventories`: Inventory items linked to products and stores

## Testing

To run tests locally:

```
poetry run pytest
```

## Project Structure

```
inventory/
├── src/
│   ├── adapters/
│   │   ├── input/
│   │   │   ├── controllers/     # API controllers (FastAPI routers)
│   │   │   ├── schemas.py       # Pydantic models for request/response
│   │   │   └── examples.py      # API documentation examples
│   │   └── output/
│   │       └── repositories/    # Database repositories
│   ├── application/
│   │   └── use_cases/           # Business logic use cases
│   ├── domain/                  # Domain entities and services
│   └── infrastructure/
│       ├── config/              # Configuration (settings, logger)
│       └── database/            # Database models and connection
├── alembic/                     # Database migration files
├── tests/                       # Test files
├── app.py                       # FastAPI application entry point
├── main.py                      # Alternative entry point
├── pyproject.toml               # Poetry dependencies
├── Dockerfile                   # Production Docker image
├── Dockerfile.test              # Test Docker image
├── docker-compose.yml           # Production compose file
├── docker-compose.with-db.yml   # Production with database
└── docker-compose.test.yml      # Test compose file
```
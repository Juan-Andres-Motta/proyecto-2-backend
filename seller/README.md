# Seller Service

Seller service built with FastAPI.

## Features

- Health check endpoint
- Root endpoint returning service name
- Seller management (create, list with pagination)
- Sales plan management (create, list with pagination)
- Hexagonal architecture with clean separation of concerns
- PostgreSQL database with SQLAlchemy ORM
- Pydantic schemas for request/response validation

## Installation

1. Ensure you have Python 3.13+ installed.
2. Install Poetry if not already installed: `curl -sSL https://install.python-poetry.org | python3 -`
3. Clone the repository and navigate to the project directory.
4. Install dependencies: `poetry install`

## Running Locally

To run the service locally:

```
poetry run uvicorn app:app --reload
```

The service will be available at `http://localhost:8000`.

## Running with Docker

### Production

```
docker-compose up --build
```

### Tests

```
docker-compose -f docker-compose.test.yml up --build
```

## API Endpoints

### Common
- `GET /`: Returns service information
- `GET /health`: Health check endpoint

### Sellers
- `POST /sellers`: Create a new seller
- `GET /sellers`: List sellers with pagination

### Sales Plans
- `POST /sales-plans`: Create a new sales plan
- `GET /sales-plans`: List sales plans with pagination

All endpoints are documented at `http://localhost:8000/docs` when running locally.

## Testing

To run tests locally:

```
poetry run pytest
```

## Project Structure

- `app.py`: Main FastAPI application
- `main.py`: CLI commands for running, migrations, and testing
- `src/`: Source code organized in hexagonal architecture
  - `adapters/`: Input/output adapters
    - `input/`: Controllers, schemas, examples
    - `output/`: Repositories
  - `application/`: Use cases and business logic
  - `domain/`: Domain entities and services
  - `infrastructure/`: Database models, config, logging
- `tests/`: Test files
- `Dockerfile`: Production Docker image
- `Dockerfile.test`: Test Docker image
- `docker-compose.yml`: Production compose file
- `docker-compose.test.yml`: Test compose file
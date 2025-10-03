# Catalog Service

Catalog service built with FastAPI following hexagonal architecture principles.

## Features

- Health check endpoint
- Root endpoint returning service name
- Provider management with CRUD operations
- PostgreSQL database with SQLAlchemy ORM
- Database migrations with Alembic
- Comprehensive test suite
- Code quality tools (flake8, black, isort)
- Docker containerization

## Architecture

This project follows **Hexagonal Architecture** (Ports & Adapters) with the following structure:

```
src/
├── domain/              # Business logic and entities
├── application/         # Use cases and application services
├── infrastructure/      # External systems (database, config)
├── adapters/
│   ├── input/          # Driving adapters (controllers, API routes)
│   └── output/         # Driven adapters (repositories)
```

## Installation

1. Ensure you have Python 3.13+ installed.
2. Install Poetry if not already installed: `curl -sSL https://install.python-poetry.org | python3 -`
3. Clone the repository and navigate to the project directory.
4. Install dependencies: `poetry install`

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Database
DATABASE_URL=postgresql://postgres:password@catalog-db:5432/catalog

# For local development
# DATABASE_URL=postgresql://juan:@localhost:5432/catalog
```

### Poetry Virtual Environment

Poetry is configured to create virtual environments in the project directory:

```bash
poetry config virtualenvs.in-project true
poetry install
source .venv/bin/activate  # or poetry shell
```

## Database Setup

### Local Development

1. Start PostgreSQL database (locally or via Docker)
2. Run migrations: `poetry run alembic upgrade head`

### Docker Environment

The project includes Docker Compose configurations:

- `docker-compose.yml`: Production setup with PostgreSQL
- `docker-compose.with-db.yml`: Development with database
- `docker-compose.test.yml`: Testing environment

## Running Locally

To run the service locally:

```bash
poetry run uvicorn src.main:app --reload
```

The service will be available at `http://localhost:8000`.

## Running with Docker

### Production

```bash
docker-compose up --build
```

### Development with Database

```bash
docker-compose -f docker-compose.with-db.yml up --build
```

### Tests

```bash
docker-compose -f docker-compose.test.yml up --build
```

## API Endpoints

- `GET /`: Returns service information
- `GET /health`: Health check endpoint
- `POST /provider`: Create a new provider
- `GET /providers`: List providers with pagination

## Database Migrations

### Create Migration

```bash
poetry run alembic revision --autogenerate -m "migration message"
```

### Apply Migrations

```bash
poetry run alembic upgrade head
```

### Check Status

```bash
poetry run alembic current
```

## Code Quality

The project includes automated code quality tools:

### Linting and Formatting

```bash
poetry run flake8 .      # Lint code
poetry run black .       # Format code
poetry run isort .       # Sort imports
```

### Configuration

Tools are configured in `pyproject.toml` with appropriate exclusions for virtual environments and migration files.

## Testing

### Run Tests

```bash
poetry run pytest
```

### Test Structure

- **Unit Tests**: Business logic with mocked dependencies
- **Integration Tests**: Database operations with SQLite
- **API Tests**: Full request/response cycles

### Test Database

Tests use SQLite in-memory database for fast, isolated testing.

## Project Structure

```
src/
├── domain/                          # Business entities and logic
├── application/                     # Use cases and services
├── infrastructure/
│   ├── database/
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   └── config.py               # Database configuration
│   └── config/
│       └── settings.py             # Application settings
├── adapters/
│   ├── input/
│   │   ├── controllers/            # API controllers
│   │   └── schemas.py              # Pydantic schemas
│   └── output/
│       └── repositories/           # Data repositories
├── main.py                         # Application entry point

tests/                              # Test suite
alembic/                           # Database migrations
```

## Development Workflow

1. Create feature branch
2. Implement changes following hexagonal architecture
3. Add/update tests
4. Run code quality checks: `poetry run black . && poetry run isort . && poetry run flake8 .`
5. Run tests: `poetry run pytest`
6. Create migration if needed: `poetry run alembic revision --autogenerate -m "message"`
7. Commit changes

## Dependencies

### Core
- **FastAPI**: Modern async web framework
- **SQLAlchemy**: SQL toolkit and ORM
- **Pydantic**: Data validation
- **Alembic**: Database migration tool

### Development
- **pytest**: Testing framework
- **black**: Code formatter
- **flake8**: Linter
- **isort**: Import sorter

### Database
- **asyncpg**: Async PostgreSQL driver
- **aiosqlite**: Async SQLite driver (for testing)
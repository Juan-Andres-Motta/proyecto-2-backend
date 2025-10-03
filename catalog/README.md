# Catalog Service

Catalog service built with FastAPI.

## Features

- Health check endpoint
- Root endpoint returning service name

## Installation

1. Ensure you have Python 3.13+ installed.
2. Install Poetry if not already installed: `curl -sSL https://install.python-poetry.org | python3 -`
3. Clone the repository and navigate to the project directory.
4. Install dependencies: `poetry install`

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

### Tests

```
docker-compose -f docker-compose.test.yml up --build
```

## API Endpoints

- `GET /`: Returns service information
- `GET /health`: Health check endpoint

## Testing

To run tests locally:

```
poetry run pytest
```

## Project Structure

- `main.py`: Main FastAPI application
- `tests/`: Test files
- `Dockerfile`: Production Docker image
- `Dockerfile.test`: Test Docker image
- `docker-compose.yml`: Production compose file
- `docker-compose.test.yml`: Test compose file
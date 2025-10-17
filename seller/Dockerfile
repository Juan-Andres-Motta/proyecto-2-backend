# ============================================
# Stage 1: base - Dependencies and build
# ============================================
FROM python:3.13-slim as base

WORKDIR /app

# Set PYTHONPATH
ENV PYTHONPATH=/app

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies (without dev dependencies for production)
RUN poetry install --no-root --no-interaction --no-ansi

# Copy source code
COPY . .

# ============================================
# Stage 2: app - Run the application
# ============================================
FROM base as app

# Expose port
EXPOSE 8000

# Run the application
CMD ["poetry", "run", "python", "main.py", "runserver", "--port", "8000", "--reload"]

# ============================================
# Stage 3: migrate - Run migrations
# ============================================
FROM base as migrate

# Run migrations
CMD ["poetry", "run", "python", "main.py", "migrate"]

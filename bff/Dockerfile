FROM python:3.13-slim

WORKDIR /app

# Set PYTHONPATH
ENV PYTHONPATH=/app

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry

# Configure Poetry to not use virtualenv (container is already isolated)
RUN poetry config virtualenvs.create false

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies (without dev dependencies for production)
RUN poetry install --no-interaction --no-ansi

# Copy source code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "main.py", "runserver", "--port", "8000", "--reload"]
FROM python:3.13-slim

WORKDIR /app

# Set PYTHONPATH
ENV PYTHONPATH=/app

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies (without dev dependencies for production)
RUN poetry install --no-root --no-interaction --no-ansi

# Copy source code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["poetry", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
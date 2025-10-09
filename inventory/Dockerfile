FROM python:3.13-slim

WORKDIR /app

# Set PYTHONPATH
ENV PYTHONPATH=/app

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies (without dev dependencies for production)
RUN poetry install --no-interaction --no-ansi

# Copy source code
COPY . .

# Expose port
EXPOSE 8004

# Run the application
CMD ["poetry", "run", "python", "main.py", "runserver", "--port", "8004", "--reload"]
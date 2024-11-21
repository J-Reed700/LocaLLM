# Use Python 3.11 slim as base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=1.6.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false

# Add Poetry to PATH
ENV PATH="$POETRY_HOME/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip3 install poetry

# Set the working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install project dependencies
RUN poetry install --no-interaction --no-ansi --no-root

# Copy application code
COPY src/ ./src/
COPY websrc/ ./websrc/


# Create necessary directories
RUN mkdir -p logs

# Set environment variables for Prometheus
ENV OTEL_SERVICE_NAME=locaLLM_server \
    OTEL_METRICS_EXPORTER=prometheus \
    OTEL_EXPORTER_PROMETHEUS_ENABLED=true \
    OTEL_EXPORTER_PROMETHEUS_PORT=8001 \
    OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true \
    PYTHONPATH=/app

# Expose ports
EXPOSE 8000
EXPOSE 8001

# Run the application
CMD ["poetry", "run", "uvicorn", "websrc.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
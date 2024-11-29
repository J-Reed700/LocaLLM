# Use Python 3.11 slim as base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=1.6.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    PGADMIN_DEFAULT_EMAIL=admin@admin.com \
    PGADMIN_DEFAULT_PASSWORD=admin \
    PYTHONPATH=/app

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

# Copy ALL application code
COPY . .

# Create necessary directories
RUN mkdir -p logs

# Set environment variables for OpenTelemetry
ENV OTEL_SERVICE_NAME=locaLLM_server \
    OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true \
    OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 \
    OTEL_EXPORTER_OTLP_PROTOCOL=grpc

# Expose ports
EXPOSE 8080 5050

# Run the application
CMD ["poetry", "run", "uvicorn", "websrc.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload" ]
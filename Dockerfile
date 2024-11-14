# Use NVIDIA's CUDA base image
FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip3 install poetry

# Set the working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml poetry.lock* /app/

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev

# Copy application code
COPY . /app

# Expose port 8000
EXPOSE 8000


# Run the application
CMD ["poetry", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

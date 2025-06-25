# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies needed for Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install poetry
RUN pip install poetry

# Configure poetry: Don't create virtual env, install to system python
RUN poetry config virtualenvs.create false

# Copy poetry files first (for better caching)
COPY pyproject.toml poetry.lock ./

# Install dependencies only (without dev dependencies and without the current project)
RUN poetry install --only=main --no-root

# Copy project
COPY . /app/

# Create a simple health check script
RUN echo '#!/bin/bash\ncurl -f http://localhost:8000/health/ || exit 1' > /healthcheck.sh && chmod +x /healthcheck.sh

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /healthcheck.sh

# Expose port
EXPOSE 8000

# Run app
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"] 
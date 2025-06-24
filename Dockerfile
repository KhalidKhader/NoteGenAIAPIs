# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install poetry
RUN pip install poetry

# Copy poetry dependency files
COPY poetry.lock pyproject.toml /app/

# Install dependencies
RUN poetry install --no-dev

# Copy project
COPY . /app/

# Expose port
EXPOSE 8000

# Run app
CMD ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"] 
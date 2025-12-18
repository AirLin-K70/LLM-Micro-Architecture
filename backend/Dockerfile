FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from backend directory (assuming build context is project root)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend code into /app/backend to preserve package structure
COPY backend /app/backend

# Set PYTHONPATH to include /app so "backend" module is found
ENV PYTHONPATH=/app

# Default command (can be overridden)
CMD ["python", "-m", "backend.gateway_service.main"]

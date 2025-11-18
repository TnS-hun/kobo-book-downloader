FROM python:3.11-slim

# Set metadata for Unraid / OCI
LABEL maintainer="chemicalsno"
LABEL description="Kobo Book Downloader with Flask web UI for Unraid and other NAS/Docker hosts"
LABEL version="1.0.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV HOME=/config

# Install system dependencies and gosu for user mapping
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libssl-dev \
    curl \
    ca-certificates \
    gosu \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for persistent data
RUN mkdir -p /config /downloads

# Ensure script is executable
RUN chmod +x kobo-book-downloader 2>/dev/null || true \
    && chmod +x /app/entrypoint.sh

# Default entrypoint: run CLI with args from KBD_COMMAND
ENTRYPOINT ["/app/entrypoint.sh"]

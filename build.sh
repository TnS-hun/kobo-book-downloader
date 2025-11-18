#!/bin/bash

# Build script for kobo-book-downloader container
# This script builds and tests the Docker container

set -e

echo "[INFO] Building kobo-book-downloader container..."

# Build the Docker image
docker build -t kobo-book-downloader:latest .

echo "[OK] Build completed successfully!"

# Create test directories
echo "[INFO] Creating test directories..."
mkdir -p test-config test-downloads

# Run a quick test to ensure the container starts
echo "[INFO] Running container test..."
docker run --rm \
  --name kobo-test \
  -v "$(pwd)/test-config:/config" \
  -v "$(pwd)/test-downloads:/downloads" \
  -e PUID=$(id -u) \
  -e PGID=$(id -g) \
  kobo-book-downloader:latest \
  python kobo-book-downloader --help > /dev/null

echo "[OK] Container test passed!"

# Clean up test directories
rm -rf test-config test-downloads

echo "[INFO] Container is ready for deployment!"
echo ""
echo "To run with docker-compose:"
echo "  docker-compose up -d"
echo ""
echo "To run manually:"
echo "  docker run -d --name kobo-book-downloader -p 5000:5000 -v \$(pwd)/config:/config -v \$(pwd)/downloads:/downloads kobo-book-downloader:latest"

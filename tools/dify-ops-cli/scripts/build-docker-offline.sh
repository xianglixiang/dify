#!/bin/bash
# Build offline Docker image for dify-ops-cli
# This script creates a Docker image and exports it as a tar.gz file
# for deployment in offline/air-gapped environments

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VERSION="v0.1.0"
IMAGE_NAME="dify-ops-cli"
OUTPUT_DIR="$PROJECT_ROOT/dist"

echo "========================================="
echo "Building Docker Offline Image"
echo "========================================="
echo "Image: $IMAGE_NAME:$VERSION"
echo "Project: $PROJECT_ROOT"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Build Docker image
echo "Step 1/3: Building Docker image..."
cd "$PROJECT_ROOT"
docker build -t "$IMAGE_NAME:$VERSION" .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed"
    exit 1
fi

echo "✓ Docker image built successfully"
echo ""

# Save Docker image to tar file
echo "Step 2/3: Saving Docker image..."
docker save "$IMAGE_NAME:$VERSION" -o "$OUTPUT_DIR/$IMAGE_NAME-$VERSION.tar"

if [ $? -ne 0 ]; then
    echo "❌ Docker save failed"
    exit 1
fi

echo "✓ Docker image saved to tar file"
echo ""

# Compress the tar file
echo "Step 3/3: Compressing image..."
gzip -f "$OUTPUT_DIR/$IMAGE_NAME-$VERSION.tar"

if [ $? -ne 0 ]; then
    echo "❌ Compression failed"
    exit 1
fi

echo "✓ Image compressed"
echo ""

# Show result
IMAGE_FILE="$OUTPUT_DIR/$IMAGE_NAME-$VERSION.tar.gz"
IMAGE_SIZE=$(du -h "$IMAGE_FILE" | cut -f1)

echo "========================================="
echo "✓ Docker offline image ready!"
echo "========================================="
echo "File: $IMAGE_FILE"
echo "Size: $IMAGE_SIZE"
echo ""
echo "To load in offline environment:"
echo "  docker load -i $IMAGE_NAME-$VERSION.tar.gz"
echo ""
echo "To run:"
echo "  docker run -v \$(pwd):/config $IMAGE_NAME:$VERSION apply /config/config.yaml"
echo "========================================="

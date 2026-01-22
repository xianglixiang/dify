#!/bin/bash
# Build offline package for dify-ops-cli
# This script downloads all dependencies as wheel files
# for installation in offline/air-gapped environments

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
WHEELS_DIR="$PROJECT_ROOT/dist/wheels"
VERSION="v0.1.0"
OUTPUT_FILE="dify-ops-cli-offline-$VERSION.tar.gz"

echo "========================================="
echo "Building Offline Package"
echo "========================================="
echo "Project: $PROJECT_ROOT"
echo "Output: $OUTPUT_FILE"
echo ""

# Check if requirements.txt exists
if [ ! -f "$PROJECT_ROOT/requirements.txt" ]; then
    echo "❌ requirements.txt not found"
    echo "Please run: uv pip freeze | grep -v '^-e' > requirements.txt"
    exit 1
fi

# Create wheels directory
echo "Step 1/4: Creating wheels directory..."
rm -rf "$WHEELS_DIR"
mkdir -p "$WHEELS_DIR"
echo "✓ Directory created"
echo ""

# Download dependencies for Linux x86_64 (user's platform)
echo "Step 2/4: Downloading dependencies for linux_x86_64..."
cd "$PROJECT_ROOT"

uv pip download \
  -r requirements.txt \
  --dest "$WHEELS_DIR" \
  --python-version 3.11 \
  --only-binary=:all: \
  --platform manylinux2014_x86_64

if [ $? -ne 0 ]; then
    echo "❌ Download failed"
    exit 1
fi

echo "✓ Dependencies downloaded"
echo ""

# Copy project source and essential files
echo "Step 3/4: Copying project files..."
cp -r "$PROJECT_ROOT/dify_ops_cli" "$WHEELS_DIR/"
cp "$PROJECT_ROOT/pyproject.toml" "$WHEELS_DIR/"
cp "$PROJECT_ROOT/README.md" "$WHEELS_DIR/"
cp "$PROJECT_ROOT/.env.example" "$WHEELS_DIR/"
cp -r "$PROJECT_ROOT/examples" "$WHEELS_DIR/"

# Copy installation script
cp "$SCRIPT_DIR/install-offline.sh" "$WHEELS_DIR/"
chmod +x "$WHEELS_DIR/install-offline.sh"

echo "✓ Project files copied"
echo ""

# Create tarball
echo "Step 4/4: Creating tarball..."
cd "$PROJECT_ROOT/dist"
tar -czf "$OUTPUT_FILE" -C "$WHEELS_DIR" .

if [ $? -ne 0 ]; then
    echo "❌ Tarball creation failed"
    exit 1
fi

echo "✓ Tarball created"
echo ""

# Show result
PACKAGE_FILE="$PROJECT_ROOT/dist/$OUTPUT_FILE"
PACKAGE_SIZE=$(du -h "$PACKAGE_FILE" | cut -f1)
WHEEL_COUNT=$(ls -1 "$WHEELS_DIR"/*.whl 2>/dev/null | wc -l)

echo "========================================="
echo "✓ Offline package ready!"
echo "========================================="
echo "File: $PACKAGE_FILE"
echo "Size: $PACKAGE_SIZE"
echo "Wheels: $WHEEL_COUNT packages"
echo ""
echo "To install in offline environment:"
echo "  1. tar -xzf $OUTPUT_FILE"
echo "  2. cd wheels"
echo "  3. ./install-offline.sh"
echo "========================================="

# Clean up wheels directory (keep only the tarball)
rm -rf "$WHEELS_DIR"

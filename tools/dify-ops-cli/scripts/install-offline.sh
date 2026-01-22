#!/bin/bash
# Install dify-ops-cli in offline environment
# This script installs the package and all dependencies from local wheel files

set -e

CURRENT_DIR="$(pwd)"

echo "========================================="
echo "Dify Ops CLI - Offline Installation"
echo "========================================="
echo ""

# Check if wheel files exist
if [ ! -f *.whl ]; then
    echo "❌ No wheel files found in current directory"
    echo "Please extract the offline package first:"
    echo "  tar -xzf dify-ops-cli-offline-v0.1.0.tar.gz"
    exit 1
fi

# Check if Python 3.11+ is available
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
REQUIRED_VERSION="3.11"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
    echo "❌ Python 3.11+ is required"
    echo "Current version: $PYTHON_VERSION"
    exit 1
fi

echo "✓ Python $(python3 --version) detected"
echo ""

# Create virtual environment
echo "Step 1/3: Creating virtual environment..."
if [ -d ".venv" ]; then
    echo "Virtual environment already exists, removing..."
    rm -rf .venv
fi

python3 -m venv .venv

if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment"
    exit 1
fi

echo "✓ Virtual environment created"
echo ""

# Activate virtual environment
echo "Step 2/3: Activating virtual environment..."
source .venv/bin/activate

if [ $? -ne 0 ]; then
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

echo "✓ Virtual environment activated"
echo ""

# Install dependencies from wheels
echo "Step 3/3: Installing packages from wheels..."
echo "This may take a few minutes..."
echo ""

# Install all wheel files
pip install --no-index --find-links="." *.whl

if [ $? -ne 0 ]; then
    echo "❌ Installation failed"
    exit 1
fi

# Install the dify-ops-cli package itself (from current directory)
if [ -f "pyproject.toml" ]; then
    pip install --no-index --find-links="." .

    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dify-ops-cli"
        exit 1
    fi
fi

echo "✓ Installation complete"
echo ""

# Verify installation
echo "Verifying installation..."
if command -v dify-ops &> /dev/null; then
    VERSION=$(dify-ops --version 2>&1)
    echo "✓ dify-ops installed: $VERSION"
else
    echo "⚠ Warning: dify-ops command not found in PATH"
    echo "Try: source .venv/bin/activate"
fi

echo ""
echo "========================================="
echo "✓ Installation successful!"
echo "========================================="
echo ""
echo "To use dify-ops:"
echo "  1. Activate the virtual environment:"
echo "     source .venv/bin/activate"
echo ""
echo "  2. Run dify-ops commands:"
echo "     dify-ops --help"
echo "     dify-ops config validate config.yaml"
echo "     dify-ops apply config.yaml"
echo ""
echo "  3. Deactivate when done:"
echo "     deactivate"
echo "========================================="

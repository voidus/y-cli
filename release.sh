#!/bin/bash
set -e  # Exit on error

# Clean any existing dist files
rm -rf dist/

# Build the package using uv
uv build

# Create target directory if it doesn't exist
TARGET_DIR="/Users/mac/Nutstore Files/luohy15-data/chat"
mkdir -p "$TARGET_DIR"

# Copy distribution files
cp dist/*.tar.gz dist/*.whl "$TARGET_DIR"

echo "Release files copied successfully to $TARGET_DIR"

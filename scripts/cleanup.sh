#!/usr/bin/env bash
# Workspace cleanup script for Reference Toolkit

set -e

echo "=== Reference Toolkit Workspace Cleanup ==="
echo ""

# Function to remove files if they exist
remove_if_exists() {
    for file in "$@"; do
        if [ -e "$file" ]; then
            rm -rf "$file"
            echo "✓ Removed: $file"
        fi
    done
}

# Clean temporary test directories
echo "1. Cleaning temporary test directories..."
remove_if_exists \
    test_rename \
    test_rename_copy \
    test_rename_real \
    cyclamates_pdfs \
    cyclamates_pdfs_enhanced \
    docker_test \
    downloaded_pdfs \
    pdfs_with_lboro_vpn \
    data

# Clean log files
echo ""
echo "2. Cleaning log files..."
remove_if_exists *.log

# Clean temporary CSV files
echo ""
echo "3. Cleaning temporary data files..."
remove_if_exists \
    cyclamates_resolved.csv \
    refs_with_doi.csv \
    low_confidence_refs.csv \
    unresolved_refs.csv \
    "Cyclamates full text screening NOT found.txt" \
    "Cyclamates full text screening URL.txt"

# Clean build artifacts
echo ""
echo "4. Cleaning build artifacts..."
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
echo "✓ Removed build artifacts"

# Clean coverage files
echo ""
echo "5. Cleaning coverage files..."
remove_if_exists \
    .coverage \
    .coverage.* \
    htmlcov \
    .pytest_cache

echo ""
echo "=== Cleanup complete! ==="
echo ""
echo "Workspace is now clean. Only essential project files remain."

#!/bin/bash
# Reference Toolkit - Docker Quick Start Script

set -e

echo "================================================"
echo "Reference Toolkit - Docker Quick Start"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

echo -e "${GREEN}✓ Docker found${NC}"

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}Error: Docker is not running${NC}"
    echo "Please start Docker Desktop or the Docker daemon"
    exit 1
fi

echo -e "${GREEN}✓ Docker is running${NC}"
echo ""

# Create necessary directories
echo "Creating data directories..."
mkdir -p data output
echo -e "${GREEN}✓ Directories created${NC}"
echo ""

# Build Docker image
echo "Building Docker image (this may take a few minutes)..."
if docker build -t reference-toolkit:latest . ; then
    echo -e "${GREEN}✓ Docker image built successfully${NC}"
else
    echo -e "${RED}✗ Docker build failed${NC}"
    exit 1
fi

echo ""
echo "================================================"
echo -e "${GREEN}Setup Complete!${NC}"
echo "================================================"
echo ""
echo "Quick Start Commands:"
echo ""
echo "1. Search for papers:"
echo "   docker run --rm -v \$(pwd)/data:/data reference-toolkit \\"
echo "     search \"artificial sweeteners\" -o /output/results.csv"
echo ""
echo "2. Resolve references:"
echo "   docker run --rm -v \$(pwd)/data:/data reference-toolkit \\"
echo "     resolve /data/refs.txt -o /output/resolved.csv"
echo ""
echo "3. Download PDFs:"
echo "   docker run --rm -v \$(pwd)/data:/data reference-toolkit \\"
echo "     download /output/resolved.csv --download-dir /output/pdfs"
echo ""
echo "4. Run full pipeline:"
echo "   docker run --rm -v \$(pwd)/data:/data reference-toolkit \\"
echo "     pipeline /data/refs.txt --download-dir /output/pdfs"
echo ""
echo "5. Using docker-compose (recommended):"
echo "   docker-compose run run search \"query\" -o /output/results.csv"
echo ""
echo "For more information, see README_DOCKER.md"
echo "================================================"

#!/bin/bash
# Example Workflow: Process References with Docker
# This script demonstrates a typical workflow for processing reference lists

set -e

# Configuration
INPUT_FILE="data/references.txt"
OUTPUT_DIR="output"
PDF_DIR="$OUTPUT_DIR/pdfs"
EMAIL="your-email@example.com"  # Change this!

echo "========================================"
echo "Reference Toolkit - Docker Workflow"
echo "========================================"
echo ""

# Check if input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file not found: $INPUT_FILE"
    echo "Please add your reference list to data/references.txt"
    exit 1
fi

echo "Input file: $INPUT_FILE"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Step 1: Resolve references to DOIs
echo "Step 1: Resolving references to DOIs..."
docker run --rm \
    -v "$(pwd)/data:/data" \
    -v "$(pwd)/output:/output" \
    -e REFERENCE_TOOLKIT_EMAIL="$EMAIL" \
    reference-toolkit \
    resolve "/data/$(basename "$INPUT_FILE")" \
    -o "/output/resolved.csv"

echo "✓ Resolution complete"
echo ""

# Step 2: Download PDFs
echo "Step 2: Downloading PDFs..."
docker run --rm \
    -v "$(pwd)/data:/data" \
    -v "$(pwd)/output:/output" \
    -e REFERENCE_TOOLKIT_EMAIL="$EMAIL" \
    reference-toolkit \
    download "/output/resolved.csv" \
    --download-dir "/output/pdfs"

echo "✓ Download complete"
echo ""

# Step 3: Convert to BibTeX
echo "Step 3: Converting to BibTeX..."
docker run --rm \
    -v "$(pwd)/data:/data" \
    -v "$(pwd)/output:/output" \
    reference-toolkit \
    convert "/output/resolved.csv" \
    -o "/output/papers.bib" \
    --format bibtex

echo "✓ Conversion complete"
echo ""

# Summary
echo "========================================"
echo "Workflow Complete!"
echo "========================================"
echo ""
echo "Results:"
echo "  - Resolved DOIs: output/resolved.csv"
echo "  - Downloaded PDFs: output/pdfs/"
echo "  - BibTeX file: output/papers.bib"
echo ""
echo "PDF count:"
ls -1 "$PDF_DIR"/*.pdf 2>/dev/null | wc -l
echo ""
echo "Next steps:"
echo "  1. Review the CSV file for low-confidence matches"
echo "  2. Import PDFs into your reference manager"
echo "  3. Use the BibTeX file for citations"
echo "========================================"

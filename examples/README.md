# Examples

This directory contains usage examples for the Reference Toolkit.

## Available Examples

### Python Workflow
**File**: `example_workflow.py`

Demonstrates a complete workflow:
1. Searching for papers
2. Resolving references to DOIs
3. Downloading PDFs
4. Renaming PDFs using metadata

**Usage**:
```bash
python examples/example_workflow.py
```

### Shell Script
**File**: `example-workflow.sh`

Bash script demonstrating CLI usage for common workflows.

**Usage**:
```bash
bash examples/example-workflow.sh
```

## Quick Start Examples

### Search for Papers
```bash
reftool search "machine learning protein folding" --limit 10
```

### Resolve References
```bash
reftool resolve tests/fixtures/sample_refs.txt --output resolved.csv
```

### Download PDFs
```bash
reftool download resolved.csv --download-dir pdfs/
```

### Rename PDFs
```bash
reftool rename pdfs/ --dry-run  # Preview changes
reftool rename pdfs/             # Actually rename
```

### Full Pipeline
```bash
reftool pipeline tests/fixtures/sample_refs.txt \
    --download-dir pdfs/ \
    --bibtex
```

## Creating Your Own Workflows

### Basic Script Template
```python
#!/usr/bin/env python3
from pathlib import Path
from reference_toolkit.config import Config
from reference_toolkit.search import SearchEngine

# Create configuration
config = Config(
    email="your@email.com",
    search_limit=10,
)

# Use the toolkit
search_engine = SearchEngine(config)
results = search_engine.search(
    query="your query here",
    limit=5,
)
```

### Batch Processing Template
```bash
#!/bin/bash
# Process multiple reference files
for file in refs/*.txt; do
    echo "Processing $file..."
    reftool resolve "$file" --output "resolved/$(basename $file .txt).csv"
done
```

## Tips

1. **Always use --dry-run first** for rename operations
2. **Check confidence scores** after resolve operations
3. **Use --resume** for long-running downloads
4. **Monitor logs** for troubleshooting
5. **Test with small datasets** first

## Need More Examples?

Check the documentation:
- [PDF Renaming Guide](../docs/PDF_RENAMING_GUIDE.md)
- [Docker Usage](../docs/DOCKER_USAGE.md)
- [Enhanced Features](../docs/ENHANCED_ACCESS_FEATURES.md)

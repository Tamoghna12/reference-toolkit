# Reference Toolkit - Docker Guide

Run the Reference Toolkit in a Docker container for maximum portability across any system.

## Quick Start

### 1. Build the Docker Image

```bash
docker build -t reference-toolkit:latest .
```

### 2. Run Commands

#### Search for papers
```bash
docker run --rm -v $(pwd)/data:/data reference-toolkit \
  search "artificial sweeteners cyclamates" \
  -o /output/search_results.csv
```

#### Resolve references to DOIs
```bash
docker run --rm -v $(pwd)/data:/data reference-toolkit \
  resolve /data/references.txt \
  -o /output/resolved.csv
```

#### Download PDFs
```bash
docker run --rm -v $(pwd)/data:/data reference-toolkit \
  download /data/resolved.csv \
  --download-dir /output/pdfs
```

#### Run full pipeline
```bash
docker run --rm -v $(pwd)/data:/data reference-toolkit \
  pipeline /data/references.txt \
  --download-dir /output/pdfs
```

## Using Docker Compose (Recommended)

### 1. Start the container

```bash
docker-compose up -d
```

### 2. Run commands inside container

```bash
# Search
docker-compose run run search "cyclamates" -o /output/results.csv

# Resolve
docker-compose run run resolve /data/refs.txt -o /output/resolved.csv

# Download
docker-compose run run download /output/resolved.csv --download-dir /output/pdfs

# Pipeline
docker-compose run run pipeline /data/refs.txt --download-dir /output/pdfs
```

### 3. Stop the container

```bash
docker-compose down
```

## Directory Structure

```
.
├── Dockerfile              # Container definition
├── docker-compose.yml      # Orchestration
├── .dockerignore          # Exclude from build
├── data/                  # Input files (mount point)
│   ├── references.txt     # Your reference lists
│   └── papers.bib         # BibTeX files
└── output/                # Output files (mount point)
    ├── resolved.csv       # DOIs
    ├── search_results.csv # Search results
    └── pdfs/              # Downloaded PDFs
```

## Common Workflows

### Workflow 1: Resolve and Download

```bash
# 1. Copy your references to data/
cp "Cyclamates full text screening NOT found.txt" data/

# 2. Run pipeline
docker-compose run run pipeline \
  /data/Cyclamates\ full\ text\ screening\ NOT\ found.txt \
  --download-dir /output/pdfs

# 3. Check results
ls -la output/pdfs/
```

### Workflow 2: Search New Papers

```bash
# Search for papers
docker-compose run run search \
  "cyclamates artificial sweeteners" \
  --limit 50 \
  -o /output/search_results.csv

# Convert to BibTeX
docker-compose run run convert \
  /output/search_results.csv \
  -o /output/papers.bib \
  --format bibtex
```

### Workflow 3: Interactive Shell

```bash
# Get an interactive shell in the container
docker-compose run run bash

# Now you can run commands directly
reftool --help
reftool search "cyclamates" -o results.csv
reftool resolve refs.txt -o resolved.csv
```

## Configuration

### Environment Variables

```bash
# Set email for API requests
docker run -e REFERENCE_TOOLKIT_EMAIL=your@email.com \
  reference-toolkit search "query"

# Set confidence threshold
docker run -e REFERENCE_TOOLKIT_CONFIDENCE=70.0 \
  reference-toolkit resolve refs.txt

# Set request timeout
docker run -e REFERENCE_TOOLKIT_TIMEOUT=60 \
  reference-toolkit download resolved.csv
```

### Volume Mounts

```bash
# Mount custom input/output directories
docker run --rm \
  -v /path/to/inputs:/data \
  -v /path/to/outputs:/output \
  reference-toolkit \
  pipeline /data/refs.txt --download-dir /output/pdfs
```

## Tips and Tricks

### 1. Create an alias for convenience

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
alias reftool='docker run --rm -v $(pwd)/data:/data -v $(pwd)/output:/output reference-toolkit'
```

Now you can run:
```bash
reftool search "cyclamates" -o output/results.csv
```

### 2. Run in background

```bash
# For long-running downloads
docker run -d \
  -v $(pwd)/data:/data \
  --name reftool-download \
  reference-toolkit \
  download /data/resolved.csv --download-dir /output/pdfs

# Check logs
docker logs -f reftool-download

# See progress
docker exec reftool-download ls -la /output/pdfs/ | wc -l
```

### 3. Clean up

```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove all unused data
docker system prune -a
```

## Troubleshooting

### Issue: Permission denied on volume mounts

**Solution:**
```bash
# Fix permissions on host
sudo chown -R $USER:$USER data/ output/

# Or run with user ID
docker run --user $(id -u):$(id -g) ...
```

### Issue: Container can't access internet

**Solution:**
```bash
# Use host network
docker run --network host ...

# Or specify DNS
docker run --dns 8.8.8.8 --dns 8.8.4.4 ...
```

### Issue: Out of memory

**Solution:**
```bash
# Increase memory limit
docker run --memory=4g ...

# Or in docker-compose.yml
services:
  reference-toolkit:
    deploy:
      resources:
        limits:
          memory: 4G
```

### Issue: Slow downloads

**Solution:**
```bash
# Increase timeout
docker run -e REFERENCE_TOOLKIT_TIMEOUT=120 ...

# Or run with more CPUs
docker run --cpus=4 ...
```

## Advanced: Push to Registry

### Build and tag
```bash
docker build -t your-registry/reference-toolkit:latest .
```

### Push to registry
```bash
docker push your-registry/reference-toolkit:latest
```

### Pull and run on any system
```bash
docker pull your-registry/reference-toolkit:latest
docker run --rm -v $(pwd)/data:/data your-registry/reference-toolkit \
  search "cyclamates"
```

## Performance Tips

1. **Use docker-compose** for better resource management
2. **Mount volumes** for input/output (don't COPY into image)
3. **Use --rm** flag to auto-remove containers after use
4. **Limit resources** to prevent container from eating all RAM
5. **Use environment variables** for configuration instead of rebuilding

## Security Best Practices

1. ✅ Container runs as non-root user (rtuser)
2. ✅ Minimal base image (python:3.12-slim)
3. ✅ No unnecessary packages installed
4. ✅ Read-only root filesystem (can be enabled)
5. ⚠️ Don't mount sensitive directories as volumes
6. ⚠️ Review .dockerignore to prevent secrets in image

## Support

For issues specific to Docker usage:
1. Check Docker logs: `docker logs <container>`
2. Verify volumes: `docker inspect <container> | grep Mounts`
3. Test basic functionality: `docker run reference-toolkit reftool --help`
4. Check container stats: `docker stats`

For general Reference Toolkit issues, see main README.md.

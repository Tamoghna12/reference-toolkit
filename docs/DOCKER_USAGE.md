# Reference Toolkit - Docker Quick Reference

## Quick Start (30 seconds)

```bash
# 1. Build the image
docker build -t reference-toolkit:latest .

# 2. Run a command
docker run --rm -v $(pwd)/data:/data reference-toolkit \
  search "cyclamates" -o /output/results.csv
```

That's it! The tool now runs in a portable container on any system with Docker.

---

## Common Commands

### Search for Papers

```bash
docker run --rm \
  -v $(pwd)/data:/data \
  reference-toolkit \
  search "artificial sweeteners" \
  -o /output/results.csv
```

### Resolve References to DOIs

```bash
docker run --rm \
  -v $(pwd)/data:/data \
  reference-toolkit \
  resolve /data/refs.txt \
  -o /output/resolved.csv
```

### Download PDFs

```bash
docker run --rm \
  -v $(pwd)/data:/data \
  reference-toolkit \
  download /output/resolved.csv \
  --download-dir /output/pdfs
```

### Full Pipeline (One Command)

```bash
docker run --rm \
  -v $(pwd)/data:/data \
  reference-toolkit \
  pipeline /data/refs.txt \
  --download-dir /output/pdfs
```

### Rename PDF Files

```bash
# Rename PDFs in place
docker run --rm \
  -v $(pwd)/data:/data \
  reference-toolkit \
  rename /data/pdfs

# Preview changes (dry run)
docker run --rm \
  -v $(pwd)/data:/data \
  reference-toolkit \
  rename /data/pdfs --dry-run

# Copy renamed files to new directory
docker run --rm \
  -v $(pwd)/data:/data \
  reference-toolkit \
  rename /data/pdfs --output-dir /output/renamed_pdfs
```

---

## Directory Structure

```
project/
├── Dockerfile              # Container definition
├── docker-compose.yml      # Easy orchestration
├── data/                   # Your input files
│   └── refs.txt
└── output/                 # Results appear here
    ├── resolved.csv
    └── pdfs/
```

---

## Using Docker Compose (Easier)

```bash
# Start the service
docker-compose up -d

# Run commands
docker-compose run run search "query" -o /output/results.csv
docker-compose run run resolve /data/refs.txt -o /output/resolved.csv
docker-compose run run download /output/resolved.csv --download-dir /output/pdfs
docker-compose run run rename /data/pdfs --output-dir /output/renamed

# Stop when done
docker-compose down
```

---

## Tips

1. **Volume mounts**: Use `-v $(pwd)/data:/data` to access your files
2. **Auto-cleanup**: Add `--rm` to remove containers after use
3. **Background downloads**: Run without `-it` for long downloads
4. **Environment variables**: Use `-e VAR=value` to configure

---

## Platform Support

✅ **Works on:**
- Linux
- macOS
- Windows (with Docker Desktop)
- Any cloud provider (AWS, GCP, Azure)
- HPC clusters with Singularity

---

## Image Size

- **Base image**: ~150 MB (python:3.12-slim)
- **With dependencies**: ~140 MB additional
- **Final image**: ~291 MB (compressed on disk)

---

## Need Help?

Run: `docker run reference-toolkit reftool --help`

Or see: [README_DOCKER.md](README_DOCKER.md) for detailed documentation

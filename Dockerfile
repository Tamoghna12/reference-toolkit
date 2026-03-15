# Multi-stage Dockerfile for Reference Toolkit
# Stage 1: Builder
FROM python:3.12-slim as builder

# Set build arguments
ARG DEBIAN_FRONTEND=noninteractive

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim

# Set labels
LABEL maintainer="benzoic@gmail.com"
LABEL description="Reference Toolkit: discover, validate, resolve, and download academic papers"
LABEL version="1.0.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    REFERENCE_TOOLKIT_HOME=/app \
    DATA_DIR=/data

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r rtuser && useradd -r -g rtuser -u 1000 rtuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set up application
ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /app

# Copy application code
COPY --chown=rtuser:rtuser . /app

# Install the package in development mode
RUN pip install -e .

# Create data directory for volume mounts
RUN mkdir -p /data && chown -R rtuser:rtuser /data

# Switch to non-root user
USER rtuser

# Set up volumes
VOLUME ["/data"]

# Set working directory for user data
WORKDIR /data

# Default command
CMD ["reftool", "--help"]

# Health check (optional)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import reference_toolkit" || exit 1

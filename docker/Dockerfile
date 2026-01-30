# =============================================================================
# WaifuGen System - Main Dockerfile
# =============================================================================
# Multi-stage build for optimized image size
# Includes both development and runtime stages
# =============================================================================

# -----------------------------------------------------------------------------
# BUILD STAGE - Dependencies installation
# -----------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /build

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip wheel && \
    pip install --prefix=/install -r requirements.txt

# -----------------------------------------------------------------------------
# DEVELOPMENT STAGE - For local development with full tools
# -----------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS development

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBUG=1

# Install development dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    git \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code
COPY . .

# Expose ports
EXPOSE 8000 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8000/health || exit 1

# Default command
CMD ["python", "main.py"]

# -----------------------------------------------------------------------------
# RUNTIME STAGE - Optimized production image
# -----------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS runtime

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    wget \
    gnupg \
    ca-certificates \
    fonts-noto-cjk \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright browsers
RUN pip install playwright && playwright install chromium

# Create non-root user for security
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Create working directory
WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY --chown=appuser:appgroup . .

# Switch to non-root user
USER appuser

# Expose application ports
EXPOSE 8000 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8000/health || exit 1

# Default command
CMD ["python", "main.py"]

# =============================================================================
# END OF Dockerfile
# =============================================================================

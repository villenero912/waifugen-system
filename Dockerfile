# Dockerfile
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglx0 \
    libglib2.0-0 \
    libpq-dev \
    gcc \
    python3-dev \
    curl \
    unzip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (needed for Phase 2 automation)
RUN playwright install --with-deps chromium

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p logs output assets data models

# Expose API port
EXPOSE 8000

# Run the application
CMD ["python", "main.py"]

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy service file
COPY services/thumbnail_service.py /app/thumbnail_service.py

# Install Python dependencies
RUN pip install --no-cache-dir \
    flask==3.0.0 \
    pillow==10.1.0 \
    requests==2.31.0

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health')"

# Run service
CMD ["python", "thumbnail_service.py"]

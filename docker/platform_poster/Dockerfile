# Platform Poster Service Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy service file
COPY services/platform_poster.py /app/platform_poster.py

# Install dependencies
RUN pip install --no-cache-dir \
    flask==3.0.0 \
    requests==2.31.0

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')"

# Run service
CMD ["python", "platform_poster.py"]

FROM python:3.9-slim-bookworm

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Download Piper binary (v1.2.0)
WORKDIR /tmp
RUN curl -L https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_amd64.tar.gz | tar -xz && \
    mv piper/piper /usr/local/bin/piper && \
    mv piper/lib* /usr/local/lib/ && \
    rm -rf piper

# Set up library path for Piper
ENV LD_LIBRARY_PATH=/usr/local/lib

# Application setup
WORKDIR /app
COPY docker/piper/app.py .
RUN pip install --no-cache-dir flask

# Create volume for voices
RUN mkdir -p /app/voices

EXPOSE 5000

# Run the API
CMD ["python", "app.py"]

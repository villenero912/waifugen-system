FROM n8nio/n8n:latest

USER root

# Install Python3, PIP, and FFmpeg (needed for montage/media)
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    ffmpeg \
    git \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Create app directory for scripts
WORKDIR /app

# Switch back to node user
USER node

FROM n8nio/n8n:latest

USER root

# Install Python3, PIP, and FFmpeg (needed for montage/media)
RUN apk add --no-cache \
    python3 \
    py3-pip \
    ffmpeg \
    git \
    bash

# Create app directory for scripts
WORKDIR /app

# Switch back to node user
USER node

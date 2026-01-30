FROM n8nio/n8n:1

USER root

# Install dependencies using automated detection
RUN if command -v apk >/dev/null; then \
    apk add --no-cache python3 py3-pip ffmpeg git bash; \
    elif command -v apt-get >/dev/null; then \
    apt-get update && apt-get install -y python3 python3-pip ffmpeg git bash && rm -rf /var/lib/apt/lists/*; \
    else \
    echo "Unsupported package manager"; exit 1; \
    fi

# Create app directory for scripts
WORKDIR /app

# Switch back to node user
USER node

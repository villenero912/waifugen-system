#!/bin/bash

# =============================================================================
# Environment Loader Script
# =============================================================================
# This script loads environment variables from the secure .env file
# Run this before executing any scripts that require API keys
# Usage: source /workspace/jav_automation/scripts/load_env.sh
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"

if [[ -f "$ENV_FILE" ]]; then
    # Read and export each variable from .env file
    while IFS='=' read -r key value; do
        # Skip empty lines and comments
        [[ -z "$key" || "$key" =~ ^# ]] && continue
        # Export the variable
        export "$key"="$value"
    done < "$ENV_FILE"
    echo "[ENV] Environment variables loaded from $ENV_FILE"
else
    echo "[WARNING] Environment file not found: $ENV_FILE"
    echo "Run setup_env.sh first to configure API keys"
fi

#!/bin/bash

# =============================================================================
# Secure Environment Configuration Script for A2E API
# =============================================================================
# This script securely sets up environment variables for the A2E API
# without exposing sensitive credentials in shell history or process lists
# =============================================================================

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}[INFO]${NC} Setting up secure environment for A2E API..."

# Function to securely read API key
read_secure_api_key() {
    local var_name=$1
    local prompt_text=$2

    echo -e "${YELLOW}[INPUT]${NC} $prompt_text"
    read -rsp "Enter value (hidden): " value
    echo ""

    # Export to environment (current session only)
    export "$var_name"="$value"
}

# Function to save to .env file securely
save_to_env_file() {
    local env_file=$1
    local var_name=$2
    local var_value=$3

    # Create .env file with restricted permissions
    touch "$env_file"
    chmod 600 "$env_file"

    # Remove existing variable if present
    sed -i "/^${var_name}=/d" "$env_file"

    # Append new value
    echo "${var_name}='${var_value}'" >> "$env_file"

    echo -e "${GREEN}[SUCCESS]${NC} $var_name saved to $env_file"
}

# Main configuration
CONFIG_FILE="/workspace/jav_automation/.env"
ENV_FILE="/workspace/jav_automation/scripts/.env"

# Create scripts directory for env file if it doesn't exist
mkdir -p "$(dirname "$ENV_FILE")"

# Read and configure A2E API Key
if [[ -z "${VIDEO_A2E_API_KEY:-}" ]]; then
    read_secure_api_key "VIDEO_A2E_API_KEY" "Enter your A2E API Key:"
    save_to_env_file "$ENV_FILE" "VIDEO_A2E_API_KEY" "$VIDEO_A2E_API_KEY"
else
    echo -e "${GREEN}[INFO]${NC} VIDEO_A2E_API_KEY already set in environment"
    save_to_env_file "$ENV_FILE" "VIDEO_A2E_API_KEY" "$VIDEO_A2E_API_KEY"
fi

# Configure optional webhook URL for async processing
echo ""
read -rp "Enter A2E Webhook URL (optional, press Enter to skip): " webhook_url
if [[ -n "$webhook_url" ]]; then
    export "A2E_WEBHOOK_URL"="$webhook_url"
    save_to_env_file "$ENV_FILE" "A2E_WEBHOOK_URL" "$webhook_url"
fi

# Verify configuration
echo ""
echo -e "${GREEN}[INFO]${NC} Verifying configuration..."

if curl -s -H "Authorization: Bearer $VIDEO_A2E_API_KEY" \
    "${A2E_ENDPOINT:-https://api.video-a2e.ai/v1}/health" | grep -q '"status":"ok"'; then
    echo -e "${GREEN}[SUCCESS]${NC} API connection verified successfully!"
else
    echo -e "${YELLOW}[WARNING]${NC} Could not verify API connection. Please check your credentials."
fi

# Display configuration summary (without exposing sensitive data)
echo ""
echo -e "${GREEN}[INFO]${NC} Configuration Summary:"
echo "  - Config file: $ENV_FILE"
echo "  - File permissions: 600 (secure)"
echo "  - Environment variables: VIDEO_A2E_API_KEY, A2E_WEBHOOK_URL"

echo ""
echo -e "${GREEN}[SETUP COMPLETE]${NC}"
echo -e "To use in current shell, run: source $ENV_FILE"
echo -e "To use in scripts: source /workspace/jav_automation/scripts/load_env.sh"

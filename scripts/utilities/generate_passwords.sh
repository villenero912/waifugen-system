#!/bin/bash
# ============================================================================
# Password Generation Script - Security Enhanced
# ============================================================================
# Generates cryptographically secure passwords for all services
# Usage: ./generate_passwords.sh > .env.new
# ============================================================================

echo "# ============================================================================"
echo "# WAIFUGEN SYSTEM - SECURE ENVIRONMENT VARIABLES"
echo "# ============================================================================"
echo "# AUTO-GENERATED: $(date)"
echo "# SECURITY: Keep this file PRIVATE. Never commit to Git."
echo "# ============================================================================"
echo ""

echo "PROJECT_NAME=waifugen"
echo "TIMEZONE=Europe/Madrid"
echo "DEBUG=false"
echo "LOG_LEVEL=INFO"
echo ""

echo "# ============================================================================"
echo "# CRYPTOGRAPHICALLY SECURE PASSWORDS (32 bytes base64)"
echo "# ============================================================================"
echo "SECRET_KEY=$(openssl rand -base64 32)"
echo ""

echo "# PostgreSQL Credentials"
echo "POSTGRES_DB=waifugen_production"
echo "POSTGRES_USER=waifugen_user"
echo "POSTGRES_PASSWORD=$(openssl rand -base64 32)"
echo "POSTGRES_PORT=5432"
echo ""

echo "# Redis Credentials"
echo "REDIS_PASSWORD=$(openssl rand -base64 32)"
echo "REDIS_PORT=6379"
echo ""

echo "# ============================================================================"
echo "# API KEYS (REPLACE WITH YOUR ACTUAL KEYS)"
echo "# ============================================================================"
echo "A2E_API_KEY=REPLACE_WITH_YOUR_A2E_API_KEY"
echo "REPLICATE_API_TOKEN=REPLACE_WITH_YOUR_REPLICATE_TOKEN"
echo "PIXABAY_API_KEY=REPLACE_WITH_YOUR_PIXABAY_KEY"
echo ""

echo "# ============================================================================"
echo "# TELEGRAM NOTIFICATIONS (OPTIONAL)"
echo "# ============================================================================"
echo "TELEGRAM_BOT_TOKEN=REPLACE_WITH_YOUR_BOT_TOKEN"
echo "TELEGRAM_ADMIN_CHAT_ID=REPLACE_WITH_YOUR_CHAT_ID"
echo ""

echo "# ============================================================================"
echo "# SERVICES CONFIGURATION"
echo "# ============================================================================"
echo "OLLAMA_BASE_URL=http://ollama:11434"
echo ""

echo "# Grafana Admin"
echo "GRAFANA_USER=admin"
echo "GRAFANA_PASSWORD=$(openssl rand -base64 32)"
echo ""

echo "# Application"
echo "APP_PORT=8000"
echo ""

echo "# ============================================================================"
echo "# PHASE 2 - ADDITIONAL SERVICES (OPTIONAL)"
echo "# ============================================================================"
echo "# RUNPOD_API_KEY=REPLACE_WHEN_READY"
echo "# MODAL_API_KEY=REPLACE_WHEN_READY"
echo ""

echo "# ============================================================================"
echo "# SECURITY NOTES:"
echo "# - All passwords are 32-byte cryptographically secure random strings"
echo "# - Each service has UNIQUE password (defense in depth)"
echo "# - Rotate passwords every 90 days minimum"
echo "# - Use Docker Secrets in production"
echo "# ============================================================================"

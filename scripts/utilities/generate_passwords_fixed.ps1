# ============================================================================
# Password Generation Script - WaifuGen System
# ============================================================================
# Generates secure passwords for all services
# Usage: powershell -ExecutionPolicy Bypass -File generate_passwords_fixed.ps1
# ============================================================================

function Generate-SecurePassword {
    param([int]$Length = 40)
    $chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
    $password = ""
    for ($i = 0; $i -lt $Length; $i++) {
        $password += $chars[(Get-Random -Minimum 0 -Maximum $chars.Length)]
    }
    return $password
}

Write-Output "# ============================================================================"
Write-Output "# WAIFUGEN SYSTEM - SECURE ENVIRONMENT VARIABLES"
Write-Output "# ============================================================================"
Write-Output "# AUTO-GENERATED: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Output "# SECURITY: Keep this file PRIVATE. Never commit to Git."
Write-Output "# ============================================================================"
Write-Output ""

Write-Output "# ============================================================================"
Write-Output "# PROJECT CONFIGURATION"
Write-Output "# ============================================================================"
Write-Output "PROJECT_NAME=waifugen_system"
Write-Output "TIMEZONE=Europe/Madrid"
Write-Output "DEBUG=false"
Write-Output "LOG_LEVEL=INFO"
Write-Output ""

Write-Output "# ============================================================================"
Write-Output "# SECURE PASSWORDS (40-64 characters each)"
Write-Output "# ============================================================================"
Write-Output "SECRET_KEY=$(Generate-SecurePassword -Length 64)"
Write-Output ""

Write-Output "# PostgreSQL Credentials"
Write-Output "POSTGRES_DB=waifugen_production"
Write-Output "POSTGRES_USER=waifugen_user"
Write-Output "POSTGRES_PASSWORD=$(Generate-SecurePassword -Length 40)"
Write-Output "POSTGRES_PORT=5432"
Write-Output ""

Write-Output "# Redis Credentials"
Write-Output "REDIS_PASSWORD=$(Generate-SecurePassword -Length 40)"
Write-Output "REDIS_PORT=6379"
Write-Output ""

Write-Output "# Additional Security Keys"
Write-Output "JWT_SECRET=$(Generate-SecurePassword -Length 64)"
Write-Output "ENCRYPTION_KEY=$(Generate-SecurePassword -Length 64)"
Write-Output ""

Write-Output "# ============================================================================"
Write-Output "# API KEYS (REPLACE WITH YOUR ACTUAL KEYS)"
Write-Output "# ============================================================================"
Write-Output "A2E_API_KEY=sk_YOUR_A2E_API_KEY_HERE"
Write-Output "REPLICATE_API_TOKEN=r8_YOUR_REPLICATE_TOKEN_HERE"
Write-Output "PIXABAY_API_KEY=YOUR_PIXABAY_API_KEY_HERE"
Write-Output ""

Write-Output "# ============================================================================"
Write-Output "# TELEGRAM NOTIFICATIONS (OPTIONAL)"
Write-Output "# ============================================================================"
Write-Output "TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_FROM_BOTFATHER"
Write-Output "TELEGRAM_ADMIN_CHAT_ID=YOUR_CHAT_ID_NUMBER"
Write-Output ""

Write-Output "# ============================================================================"
Write-Output "# SERVICES CONFIGURATION"
Write-Output "# ============================================================================"
Write-Output "OLLAMA_BASE_URL=http://ollama:11434"
Write-Output "OLLAMA_PORT=11434"
Write-Output ""

Write-Output "# Grafana Admin"
Write-Output "GRAFANA_USER=admin"
Write-Output "GRAFANA_PASSWORD=$(Generate-SecurePassword -Length 40)"
Write-Output ""

Write-Output "# Application"
Write-Output "APP_PORT=8000"
Write-Output ""

Write-Output "# N8N Workflow Automation"
Write-Output "WEBHOOK_URL="
Write-Output ""

Write-Output "# ============================================================================"
Write-Output "# PHASE 2 - ADDITIONAL SERVICES (OPTIONAL)"
Write-Output "# ============================================================================"
Write-Output "# RUNPOD_API_KEY=YOUR_RUNPOD_API_KEY_WHEN_READY"
Write-Output "# MODAL_API_KEY=YOUR_MODAL_API_KEY_WHEN_READY"
Write-Output "# ONLYFANS_API_KEY=YOUR_OF_API_KEY_WHEN_READY"
Write-Output "# ONLYFANS_USER_ID=YOUR_OF_USER_ID"
Write-Output ""

Write-Output "# ============================================================================"
Write-Output "# SECURITY NOTES:"
Write-Output "# - All passwords are 40-64 character secure random strings"
Write-Output "# - Each service has UNIQUE password (defense in depth)"
Write-Output "# - Rotate passwords every 90 days minimum"
Write-Output "# - Generated: $(Get-Date -Format 'yyyy-MM-dd')"
Write-Output "# ============================================================================"

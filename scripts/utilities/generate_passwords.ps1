# ============================================================================
# Password Generation Script - PowerShell Native Version
# ============================================================================
# Generates cryptographically secure passwords for all services
# Usage: .\generate_passwords.ps1 > .env.new
# ============================================================================

Write-Output "# ============================================================================"
Write-Output "# WAIFUGEN SYSTEM - SECURE ENVIRONMENT VARIABLES"
Write-Output "# ============================================================================"
Write-Output "# AUTO-GENERATED: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Output "# SECURITY: Keep this file PRIVATE. Never commit to Git."
Write-Output "# ============================================================================"
Write-Output ""

Write-Output "PROJECT_NAME=waifugen"
Write-Output "TIMEZONE=Europe/Madrid"
Write-Output "DEBUG=false"
Write-Output "LOG_LEVEL=INFO"
Write-Output ""

Write-Output "# ============================================================================"
Write-Output "# CRYPTOGRAPHICALLY SECURE PASSWORDS (32 bytes base64)"
Write-Output "# ============================================================================"

# Generate random bytes and convert to base64
$secretKey = [Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
Write-Output "SECRET_KEY=$secretKey"
Write-Output ""

Write-Output "# PostgreSQL Credentials"
Write-Output "POSTGRES_DB=waifugen_production"
Write-Output "POSTGRES_USER=waifugen_user"
$postgresPass = [Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
Write-Output "POSTGRES_PASSWORD=$postgresPass"
Write-Output "POSTGRES_PORT=5432"
Write-Output ""

Write-Output "# Redis Credentials"
$redisPass = [Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
Write-Output "REDIS_PASSWORD=$redisPass"
Write-Output "REDIS_PORT=6379"
Write-Output ""

Write-Output "# ============================================================================"
Write-Output "# API KEYS (REPLACE WITH YOUR ACTUAL KEYS)"
Write-Output "# ============================================================================"
Write-Output "A2E_API_KEY=REPLACE_WITH_YOUR_A2E_API_KEY"
Write-Output "REPLICATE_API_TOKEN=REPLACE_WITH_YOUR_REPLICATE_TOKEN"
Write-Output "PIXABAY_API_KEY=REPLACE_WITH_YOUR_PIXABAY_KEY"
Write-Output ""

Write-Output "# ============================================================================"
Write-Output "# TELEGRAM NOTIFICATIONS (OPTIONAL)"
Write-Output "# ============================================================================"
Write-Output "TELEGRAM_BOT_TOKEN=REPLACE_WITH_YOUR_BOT_TOKEN"
Write-Output "TELEGRAM_ADMIN_CHAT_ID=REPLACE_WITH_YOUR_CHAT_ID"
Write-Output ""

Write-Output "# ============================================================================"
Write-Output "# SERVICES CONFIGURATION"
Write-Output "# ============================================================================"
Write-Output "OLLAMA_BASE_URL=http://ollama:11434"
Write-Output ""

Write-Output "# Grafana Admin"
Write-Output "GRAFANA_USER=admin"
$grafanaPass = [Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
Write-Output "GRAFANA_PASSWORD=$grafanaPass"
Write-Output ""

Write-Output "# Application"
Write-Output "APP_PORT=8000"
Write-Output ""

Write-Output "# ============================================================================"
Write-Output "# PHASE 2 - ADDITIONAL SERVICES (OPTIONAL)"
Write-Output "# ============================================================================"
Write-Output "# RUNPOD_API_KEY=REPLACE_WHEN_READY"
Write-Output "# MODAL_API_KEY=REPLACE_WHEN_READY"
Write-Output ""

Write-Output "# ============================================================================"
Write-Output "# SECURITY NOTES:"
Write-Output "# - All passwords are 32-byte cryptographically secure random strings"
Write-Output "# - Each service has UNIQUE password (defense in depth)"
Write-Output "# - Rotate passwords every 90 days minimum"
Write-Output "# - Use Docker Secrets in production"
Write-Output "# ============================================================================"

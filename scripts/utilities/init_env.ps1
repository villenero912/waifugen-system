################################################################################
# WaifuGen System - Automatic Environment Initialization Script
# Purpose: Generate secure passwords and create .env file automatically
################################################################################

# Color definitions for better UX
function Write-Success { Write-Host "[OK] $args" -ForegroundColor Green }
function Write-Info { Write-Host "[INFO] $args" -ForegroundColor Cyan }
function Write-Warning { Write-Host "[WARN] $args" -ForegroundColor Yellow }
function Write-Error { Write-Host "[ERROR] $args" -ForegroundColor Red }

# Banner
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Magenta
Write-Host "   WaifuGen System - Environment Initialization" -ForegroundColor Magenta
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Magenta
Write-Host ""

# Navigate to project root
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $ProjectRoot

Write-Info "Project root: $ProjectRoot"
Write-Host ""

################################################################################
# STEP 1: Check if .env already exists
################################################################################

if (Test-Path ".env") {
    Write-Warning "File .env already exists!"
    $response = Read-Host "Do you want to OVERWRITE it? (yes/NO)"
    
    if ($response -ne "yes") {
        Write-Info "Operation cancelled by user."
        Write-Host ""
        Write-Host "To view your current .env: notepad .env" -ForegroundColor Gray
        exit 0
    }
    
    # Backup existing .env
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupFile = ".env.backup.$timestamp"
    Copy-Item .env $backupFile
    Write-Success "Backup created: $backupFile"
}

################################################################################
# STEP 2: Generate secure random passwords
################################################################################

Write-Info "Generating secure passwords..."
Write-Host ""

function Generate-SecurePassword {
    param(
        [int]$Length = 32
    )
    
    # Character pool: alphanumeric + special chars
    $chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_=+[]{}|;:,.<>?"
    
    # Generate random password
    $password = -join ((1..$Length) | ForEach-Object { 
            $chars[(Get-Random -Minimum 0 -Maximum $chars.Length)]
        })
    
    return $password
}

# Generate passwords for local services
$POSTGRES_PASSWORD = Generate-SecurePassword -Length 32
$REDIS_PASSWORD = Generate-SecurePassword -Length 32
$GRAFANA_PASSWORD = Generate-SecurePassword -Length 24
$SECRET_KEY = Generate-SecurePassword -Length 64

Write-Success "PostgreSQL password: [32 characters - HIDDEN]"
Write-Success "Redis password: [32 characters - HIDDEN]"
Write-Success "Grafana password: [24 characters - HIDDEN]"
Write-Success "Secret Key: [64 characters - HIDDEN]"
Write-Host ""

################################################################################
# STEP 3: Ask for external API keys (optional)
################################################################################

Write-Info "Now we need external API keys (you can leave blank for now):"
Write-Host ""

Write-Host "-----------------------------------------------------------" -ForegroundColor DarkGray
Write-Host "[VIDEO] A2E AI Video Generation" -ForegroundColor Yellow
Write-Host "   Get your API key at: https://a2e.ai/" -ForegroundColor Gray
Write-Host "   Plan: PRO ($8.25/month)" -ForegroundColor Gray
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
$A2E_API_KEY = Read-Host "A2E API Key (or press Enter to skip)"
if ([string]::IsNullOrWhiteSpace($A2E_API_KEY)) {
    $A2E_API_KEY = "your_a2e_api_key_here"
    Write-Warning "A2E not configured - video generation will NOT work"
}
else {
    Write-Success "A2E API Key configured"
}
Write-Host ""

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host "[MUSIC] Replicate MusicGen" -ForegroundColor Yellow
Write-Host "   Get your API key at: https://replicate.com/account/api-tokens" -ForegroundColor Gray
Write-Host "   Cost: ~$0.03/reel (~$3.60/month for 120 reels)" -ForegroundColor Gray
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
$REPLICATE_API_KEY = Read-Host "Replicate API Key (or press Enter to skip)"
if ([string]::IsNullOrWhiteSpace($REPLICATE_API_KEY)) {
    $REPLICATE_API_KEY = "your_replicate_api_key_here"
    Write-Warning "Replicate not configured - will use Pixabay for music"
}
else {
    Write-Success "Replicate API Key configured"
}
Write-Host ""

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host "[MUSIC] Pixabay Music (Free Alternative)" -ForegroundColor Yellow
Write-Host "   Get your API key at: https://pixabay.com/api/docs/" -ForegroundColor Gray
Write-Host "   Cost: FREE (20,000 requests/month)" -ForegroundColor Gray
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
$PIXABAY_API_KEY = Read-Host "Pixabay API Key (or press Enter to skip)"
if ([string]::IsNullOrWhiteSpace($PIXABAY_API_KEY)) {
    $PIXABAY_API_KEY = "your_pixabay_api_key_here"
    Write-Warning "Pixabay not configured"
}
else {
    Write-Success "Pixabay API Key configured"
}
Write-Host ""

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host "[NOTIFY] Telegram Notifications (Recommended)" -ForegroundColor Yellow
Write-Host "   1. Talk to @BotFather on Telegram" -ForegroundColor Gray
Write-Host "   2. Send /newbot and follow instructions" -ForegroundColor Gray
Write-Host "   3. Get your Chat ID from @userinfobot" -ForegroundColor Gray
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
$TELEGRAM_BOT_TOKEN = Read-Host "Telegram Bot Token (or press Enter to skip)"
if ([string]::IsNullOrWhiteSpace($TELEGRAM_BOT_TOKEN)) {
    $TELEGRAM_BOT_TOKEN = "your_telegram_bot_token_here"
    Write-Warning "Telegram not configured - no production alerts"
}
else {
    Write-Success "Telegram Bot Token configured"
}

$TELEGRAM_CHAT_ID = Read-Host "Telegram Chat ID (or press Enter to skip)"
if ([string]::IsNullOrWhiteSpace($TELEGRAM_CHAT_ID)) {
    $TELEGRAM_CHAT_ID = "your_telegram_chat_id_here"
}
else {
    Write-Success "Telegram Chat ID configured"
}
Write-Host ""

################################################################################
# STEP 4: Create .env file from template
################################################################################

Write-Info "Creating .env file..."
Write-Host ""

$envContent = @"
# =============================================================================
# WaifuGen System - Environment Configuration
# =============================================================================
# GENERATED AUTOMATICALLY BY init_env.ps1
# Date: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
# =============================================================================
# SECURITY WARNING:
# - NEVER share this file with anyone
# - NEVER commit this file to Git
# - Backup securely (encrypted USB, password manager, etc.)
# =============================================================================

# --- GENERAL PROJECT SETTINGS ---
PROJECT_NAME=waifugen
TIMEZONE=Asia/Tokyo
DEBUG=false
LOG_LEVEL=INFO
SECRET_KEY=$SECRET_KEY

# --- DATABASE (POSTGRES) ---
POSTGRES_DB=waifugen_prod
POSTGRES_USER=waifugen_user
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
POSTGRES_PORT=5432

# --- CACHE (REDIS) ---
REDIS_PASSWORD=$REDIS_PASSWORD
REDIS_PORT=6379

# --- API KEYS (VIDEO GENERATION) ---
A2E_API_KEY=$A2E_API_KEY

# Optional: Qwen LLM (NOT needed if using Ollama local)
# QWEN_API_KEY=your_qwen_api_key_here

# --- MUSIC GENERATION ---
REPLICATE_API_KEY=$REPLICATE_API_KEY
PIXABAY_API_KEY=$PIXABAY_API_KEY

# --- MONITORING (TELEGRAM) ---
TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID=$TELEGRAM_CHAT_ID

# --- MONITORING (GRAFANA) ---
GRAFANA_USER=admin
GRAFANA_PASSWORD=$GRAFANA_PASSWORD

# --- OLLAMA (LOCAL LLM) ---
OLLAMA_PORT=11434
OLLAMA_BASE_URL=http://ollama:11434

# --- INFRASTRUCTURE ---
APP_PORT=8000
PROXY_URL=http://user:pass@proxy_host:port

# --- PHASE 2 MARKETING (DO NOT CONFIGURE YET) ---
WEBHOOK_URL=https://your-domain.com/webhook
ONLYFANS_USER=your_onlyfans_username
ONLYFANS_PASS=your_onlyfans_password

# =============================================================================
# SOCIAL MEDIA APIs - REQUIRED FOR POSTING (CURRENTLY NOT CONFIGURED)
# =============================================================================
# Get these credentials from the respective developer portals:
# - TikTok: https://developers.tiktok.com/
# - Instagram/Facebook: https://developers.facebook.com/
# - YouTube: https://console.cloud.google.com/

# TikTok
TIKTOK_CLIENT_KEY=your_tiktok_client_key
TIKTOK_CLIENT_SECRET=your_tiktok_client_secret
TIKTOK_ACCESS_TOKEN=your_tiktok_access_token

# Instagram/Facebook
INSTAGRAM_APP_ID=your_instagram_app_id
INSTAGRAM_APP_SECRET=your_instagram_app_secret
INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token

# YouTube
YOUTUBE_CLIENT_ID=your_youtube_client_id
YOUTUBE_CLIENT_SECRET=your_youtube_client_secret
YOUTUBE_API_KEY=your_youtube_api_key
YOUTUBE_REFRESH_TOKEN=your_youtube_refresh_token

# =============================================================================
# END OF CONFIGURATION
# =============================================================================
"@

# Write .env file
$envContent | Out-File -FilePath ".env" -Encoding UTF8 -NoNewline

Write-Success ".env file created successfully!"
Write-Host ""

################################################################################
# STEP 5: Validate configuration
################################################################################

Write-Info "Validating configuration..."
Write-Host ""

$criticalMissing = @()

if ($A2E_API_KEY -eq "your_a2e_api_key_here") {
    $criticalMissing += "A2E_API_KEY (required for video generation)"
}

if ($REPLICATE_API_KEY -eq "your_replicate_api_key_here" -and $PIXABAY_API_KEY -eq "your_pixabay_api_key_here") {
    Write-Warning "No music API configured (Replicate or Pixabay)"
}

if ($TELEGRAM_BOT_TOKEN -eq "your_telegram_bot_token_here") {
    Write-Warning "Telegram notifications disabled"
}

Write-Host "-----------------------------------------------------------" -ForegroundColor Green
Write-Host "   CONFIGURATION SUMMARY" -ForegroundColor Green
Write-Host "-----------------------------------------------------------" -ForegroundColor Green
Write-Host ""

Write-Success "Local Services (Auto-Generated Passwords):"
Write-Host "   • PostgreSQL: ✅ Configured" -ForegroundColor Green
Write-Host "   • Redis: ✅ Configured" -ForegroundColor Green
Write-Host "   • Grafana: ✅ Configured" -ForegroundColor Green
Write-Host "   • Secret Key: ✅ Configured" -ForegroundColor Green
Write-Host ""

Write-Info "External APIs:"
if ($A2E_API_KEY -ne "your_a2e_api_key_here") {
    Write-Host "   • A2E Video: [OK] Configured" -ForegroundColor Green
}
else {
    Write-Host "   • A2E Video: [ERROR] NOT Configured (BLOCKER)" -ForegroundColor Red
}

if ($REPLICATE_API_KEY -ne "your_replicate_api_key_here") {
    Write-Host "   • Replicate Music: [OK] Configured" -ForegroundColor Green
}
elseif ($PIXABAY_API_KEY -ne "your_pixabay_api_key_here") {
    Write-Host "   • Pixabay Music: [OK] Configured" -ForegroundColor Green
}
else {
    Write-Host "   • Music APIs: [WARN] Not configured" -ForegroundColor Yellow
}

if ($TELEGRAM_BOT_TOKEN -ne "your_telegram_bot_token_here") {
    Write-Host "   • Telegram: [OK] Configured" -ForegroundColor Green
}
else {
    Write-Host "   • Telegram: [WARN] Not configured" -ForegroundColor Yellow
}

Write-Host ""
Write-Warning "Social Media APIs: [ERROR] Not configured (TikTok, Instagram, YouTube)"
Write-Host "   -> These are required for automatic posting" -ForegroundColor Gray
Write-Host ""

################################################################################
# STEP 6: Save password reference (optional)
################################################################################

Write-Info "Creating password reference file (SECURE THIS)..."

$passwordRef = @"
# WaifuGen System - Password Reference
# Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
# 
# [WARNING] SECURITY WARNING: Store this file in a SECURE location!
# Recommended: 1Password, Bitwarden, encrypted USB, etc.
# 
# DO NOT commit this file to Git!
# DO NOT share via email or chat!

PostgreSQL Password: $POSTGRES_PASSWORD
Redis Password: $REDIS_PASSWORD
Grafana Password: $GRAFANA_PASSWORD
Grafana User: admin
Secret Key: $SECRET_KEY

Access Grafana at: http://localhost:3000
Username: admin
Password: $GRAFANA_PASSWORD
"@

$passwordRef | Out-File -FilePath ".env.passwords.txt" -Encoding UTF8
Write-Success "Password reference saved to: .env.passwords.txt"
Write-Warning "SAVE THIS FILE SECURELY AND DELETE FROM SERVER!"
Write-Host ""

################################################################################
# STEP 7: Final instructions
################################################################################

Write-Host "-----------------------------------------------------------" -ForegroundColor Cyan
Write-Host "   NEXT STEPS" -ForegroundColor Cyan
Write-Host "-----------------------------------------------------------" -ForegroundColor Cyan
Write-Host ""

if ($criticalMissing.Count -gt 0) {
    Write-Warning "CRITICAL APIs MISSING:"
    foreach ($missing in $criticalMissing) {
        Write-Host "   • $missing" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "To configure missing APIs:" -ForegroundColor Yellow
    Write-Host "   1. Get API keys from respective websites" -ForegroundColor Gray
    Write-Host "   2. Edit .env file: notepad .env" -ForegroundColor Gray
    Write-Host "   3. Replace placeholders with real keys" -ForegroundColor Gray
    Write-Host "   4. Save and restart Docker: docker-compose up -d" -ForegroundColor Gray
    Write-Host ""
}

Write-Info "To start the system:"
Write-Host "   docker-compose up -d" -ForegroundColor Gray
Write-Host ""

Write-Info "To view logs:"
Write-Host "   docker-compose logs -f" -ForegroundColor Gray
Write-Host ""

Write-Info "To access services:"
Write-Host "   • API: http://localhost:8000" -ForegroundColor Gray
Write-Host "   • Grafana: http://localhost:3000 (admin / [see .env.passwords.txt])" -ForegroundColor Gray
Write-Host "   • Prometheus: http://localhost:9090" -ForegroundColor Gray
Write-Host ""

Write-Success "Environment initialization completed!"
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Magenta

# ============================================================================
# Generador de Contrasenas Seguras - Sistema WaifuGen (PowerShell Nativo)
# ============================================================================
# Este script NO requiere Python - usa solo PowerShell nativo
# Genera contrasenas deterministas usando PBKDF2-HMAC-SHA256
# ============================================================================

param(
    [string]$MasterPassword = "Otoñoazul82@",
    [string]$OutputFile = ".env"
)

function Generate-DerivedPassword {
    param(
        [string]$MasterPassword,
        [string]$ServiceName,
        [int]$Length = 32
    )
    
    $saltString = "waifugen_system_${ServiceName}_2026"
    $salt = [System.Text.Encoding]::UTF8.GetBytes($saltString)
    $masterBytes = [System.Text.Encoding]::UTF8.GetBytes($MasterPassword)
    
    $pbkdf2 = New-Object System.Security.Cryptography.Rfc2898DeriveBytes(
        $masterBytes,
        $salt,
        100000,
        [System.Security.Cryptography.HashAlgorithmName]::SHA256
    )
    
    $derivedKey = $pbkdf2.GetBytes($Length)
    $base64 = [Convert]::ToBase64String($derivedKey)
    $urlSafe = $base64.Replace('+', '-').Replace('/', '_').Replace('=', '')
    
    return $urlSafe.Substring(0, [Math]::Min($Length, $urlSafe.Length))
}

Write-Host "============================================================================" -ForegroundColor Green
Write-Host "  Generador de Contrasenas Seguras - WaifuGen System" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Contrasena maestra: $MasterPassword" -ForegroundColor Yellow
Write-Host "Archivo de salida: $OutputFile" -ForegroundColor Yellow
Write-Host ""
Write-Host "Generando contrasenas seguras..." -ForegroundColor Cyan
Write-Host ""

$passwords = @{
    'POSTGRES_PASSWORD' = Generate-DerivedPassword -MasterPassword $MasterPassword -ServiceName 'postgres' -Length 40
    'REDIS_PASSWORD'    = Generate-DerivedPassword -MasterPassword $MasterPassword -ServiceName 'redis' -Length 40
    'SECRET_KEY'        = Generate-DerivedPassword -MasterPassword $MasterPassword -ServiceName 'secret_key' -Length 64
    'GRAFANA_PASSWORD'  = Generate-DerivedPassword -MasterPassword $MasterPassword -ServiceName 'grafana' -Length 40
    'JWT_SECRET'        = Generate-DerivedPassword -MasterPassword $MasterPassword -ServiceName 'jwt_secret' -Length 64
    'ENCRYPTION_KEY'    = Generate-DerivedPassword -MasterPassword $MasterPassword -ServiceName 'encryption' -Length 64
}

Write-Host "Contrasenas generadas:" -ForegroundColor Green
foreach ($key in $passwords.Keys | Sort-Object) {
    $masked = $passwords[$key].Substring(0, 8) + "..." + $passwords[$key].Substring($passwords[$key].Length - 8)
    Write-Host "  $key = $masked" -ForegroundColor Gray
}
Write-Host ""

$currentDate = Get-Date -Format "yyyy-MM-dd"
$nextRotation = (Get-Date).AddDays(90).ToString("yyyy-MM-dd")

$envContent = @"
# ============================================================================
# SISTEMA WAIFUGEN - VARIABLES DE ENTORNO
# ============================================================================
# ADVERTENCIA DE SEGURIDAD: Este archivo contiene credenciales sensibles
# NUNCA subir este archivo a Git
# ============================================================================
# Contrasenas generadas automaticamente usando contrasena maestra
# Contrasena maestra: $MasterPassword
# Fecha de generacion: $currentDate
# Algoritmo: PBKDF2-HMAC-SHA256 (100,000 iteraciones)
# ============================================================================

# ============================================================================
# CONFIGURACION DEL PROYECTO
# ============================================================================
PROJECT_NAME=waifugen_system
TIMEZONE=Europe/Madrid
DEBUG=false
LOG_LEVEL=INFO

# ============================================================================
# CREDENCIALES DE BASE DE DATOS
# ============================================================================
POSTGRES_DB=waifugen_production
POSTGRES_USER=waifugen_user
POSTGRES_PASSWORD=$($passwords['POSTGRES_PASSWORD'])
POSTGRES_PORT=5432

# ============================================================================
# CREDENCIALES DE REDIS CACHE
# ============================================================================
REDIS_PASSWORD=$($passwords['REDIS_PASSWORD'])
REDIS_PORT=6379

# ============================================================================
# CLAVE SECRETA DE LA APLICACION
# ============================================================================
SECRET_KEY=$($passwords['SECRET_KEY'])

# ============================================================================
# CLAVES ADICIONALES DE SEGURIDAD
# ============================================================================
JWT_SECRET=$($passwords['JWT_SECRET'])
ENCRYPTION_KEY=$($passwords['ENCRYPTION_KEY'])

# ============================================================================
# CONFIGURACION DE A2E API (REQUERIDO - Fase 1)
# ============================================================================
# Obten tu clave API desde: https://www.a2e.ai/account/api
A2E_API_KEY=sk_YOUR_A2E_API_KEY_HERE

# ============================================================================
# REPLICATE API (OPCIONAL - Para Generacion de Musica)
# ============================================================================
REPLICATE_API_TOKEN=r8_YOUR_REPLICATE_TOKEN_HERE

# ============================================================================
# PIXABAY API (OPCIONAL - Para Biblioteca de Musica)
# ============================================================================
PIXABAY_API_KEY=YOUR_PIXABAY_API_KEY_HERE

# ============================================================================
# NOTIFICACIONES DE TELEGRAM (REQUERIDO - Recomendado)
# ============================================================================
# Como configurar:
#   1. Crear bot: https://t.me/BotFather
#   2. Obtener token del bot desde BotFather
#   3. Obtener tu chat ID: https://t.me/userinfobot
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_FROM_BOTFATHER
TELEGRAM_ADMIN_CHAT_ID=YOUR_CHAT_ID_NUMBER

# ============================================================================
# CONFIGURACION DE OLLAMA LLM
# ============================================================================
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_PORT=11434

# ============================================================================
# MONITOREO CON GRAFANA (OPCIONAL)
# ============================================================================
GRAFANA_USER=admin
GRAFANA_PASSWORD=$($passwords['GRAFANA_PASSWORD'])

# ============================================================================
# PUERTO DE LA APLICACION
# ============================================================================
APP_PORT=8000

# ============================================================================
# N8N WORKFLOW AUTOMATION
# ============================================================================
WEBHOOK_URL=

# ============================================================================
# FASE 2 - SERVICIOS AVANZADOS (Configurar cuando sea necesario)
# ============================================================================
# RUNPOD_API_KEY=YOUR_RUNPOD_API_KEY_WHEN_READY
# MODAL_API_KEY=YOUR_MODAL_API_KEY_WHEN_READY
# ONLYFANS_API_KEY=YOUR_OF_API_KEY_WHEN_READY
# ONLYFANS_USER_ID=YOUR_OF_USER_ID

# ============================================================================
# INFORMACION DE ROTACION
# ============================================================================
# Ultima generacion: $currentDate
# Proxima rotacion: $nextRotation (+90 dias)
# Para regenerar: .\scripts\utilities\generate_passwords_native.ps1 -MasterPassword "$MasterPassword"
# ============================================================================
"@

$envContent | Out-File -FilePath $OutputFile -Encoding UTF8 -NoNewline

Write-Host "Archivo creado exitosamente: $OutputFile" -ForegroundColor Green
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Green
Write-Host "  Generacion Completada" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "IMPORTANTE - Proximos pasos:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  1. Edita el archivo $OutputFile y anade tus claves API:" -ForegroundColor White
Write-Host "     - A2E_API_KEY" -ForegroundColor Gray
Write-Host "     - TELEGRAM_BOT_TOKEN" -ForegroundColor Gray
Write-Host "     - TELEGRAM_ADMIN_CHAT_ID" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Despliega al VPS:" -ForegroundColor White
Write-Host "     .\scripts\deploy_env.ps1" -ForegroundColor Gray
Write-Host ""

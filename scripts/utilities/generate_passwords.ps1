# ============================================================================
# Generador de Contraseñas Seguras - Sistema WaifuGen (PowerShell)
# ============================================================================
# Script wrapper para ejecutar el generador de contraseñas Python
# Uso: .\generate_passwords.ps1
#      .\generate_passwords.ps1 -MasterPassword "TuContraseña" -OutputFile ".env"
# ============================================================================

param(
    [string]$MasterPassword = "Otoñoazul82@",
    [string]$OutputFile = ".env"
)

Write-Host "============================================================================" -ForegroundColor Green
Write-Host "  Generador de Contraseñas Seguras - WaifuGen System" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Green
Write-Host ""

# Verificar que Python está instalado
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
}

if (-not $pythonCmd) {
    Write-Host "ERROR: Python no está instalado" -ForegroundColor Red
    Write-Host "Por favor, instala Python 3 desde https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

Write-Host "Contraseña maestra: $MasterPassword" -ForegroundColor Yellow
Write-Host "Archivo de salida: $OutputFile" -ForegroundColor Yellow
Write-Host ""

# Obtener la ruta del script Python
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonScript = Join-Path $scriptDir "generate_passwords.py"

# Verificar que el script Python existe
if (-not (Test-Path $pythonScript)) {
    Write-Host "ERROR: No se encuentra el script generate_passwords.py" -ForegroundColor Red
    Write-Host "Ruta esperada: $pythonScript" -ForegroundColor Yellow
    exit 1
}

# Ejecutar el generador de contraseñas Python
& $pythonCmd.Source $pythonScript --master $MasterPassword --output $OutputFile

Write-Host ""
Write-Host "✅ Contraseñas generadas exitosamente" -ForegroundColor Green
Write-Host ""
Write-Host "Próximos pasos:" -ForegroundColor Yellow
Write-Host "1. Edita el archivo $OutputFile y añade tus claves API"
Write-Host "2. Despliega al VPS usando: .\scripts\deploy_env.ps1"
Write-Host ""

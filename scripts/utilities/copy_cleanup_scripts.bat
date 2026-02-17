@echo off
REM ============================================================================
REM Script para copiar archivos de limpieza al VPS - Windows
REM ============================================================================
REM Uso: copy_cleanup_scripts.bat TU_IP_VPS
REM Ejemplo: copy_cleanup_scripts.bat 165.254.0.1
REM ============================================================================

if "%1"=="" (
    echo ERROR: Debes proporcionar la IP del VPS
    echo Uso: copy_cleanup_scripts.bat TU_IP_VPS
    echo Ejemplo: copy_cleanup_scripts.bat 165.254.0.1
    exit /b 1
)

set VPS_IP=%1
set VPS_USER=root
set PROJECT_DIR=/root/waifugen_system

echo ============================================================================
echo   COPIANDO SCRIPTS DE LIMPIEZA AL VPS
echo ============================================================================
echo.
echo VPS IP: %VPS_IP%
echo Usuario: %VPS_USER%
echo.

echo Copiando scripts...
scp scripts\utilities\analyze_disk_usage.sh %VPS_USER%@%VPS_IP%:%PROJECT_DIR%/scripts/utilities/
scp scripts\utilities\cleanup_disk_space.sh %VPS_USER%@%VPS_IP%:%PROJECT_DIR%/scripts/utilities/
scp scripts\utilities\setup_log_rotation.sh %VPS_USER%@%VPS_IP%:%PROJECT_DIR%/scripts/utilities/

echo.
echo ============================================================================
echo SCRIPTS COPIADOS EXITOSAMENTE
echo ============================================================================
echo.
echo Ahora conectate al VPS y ejecuta:
echo   ssh %VPS_USER%@%VPS_IP%
echo   cd %PROJECT_DIR%
echo   bash scripts/utilities/analyze_disk_usage.sh
echo   bash scripts/utilities/cleanup_disk_space.sh
echo.
echo ============================================================================

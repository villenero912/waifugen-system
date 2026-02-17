@echo off
echo ==========================================
echo   WAIFUGEN - STARTING KARAOKE SERVICE
echo ==========================================

REM Navigate to the script's directory (project root)
cd /d "%~dp0"

echo.
echo Looking for Docker...

REM Try Method 1: Absolute Path (Most reliable on Windows)
if exist "C:\Program Files\Docker\Docker\resources\bin\docker.exe" (
    echo [OK] Docker found at standard location.
    "C:\Program Files\Docker\Docker\resources\bin\docker.exe" compose up -d --build karaoke
    goto :check_error
)

REM Try Method 2: Global PATH
echo [INFO] Standard path not found. Trying global command...
docker compose up -d --build karaoke nginx n8n

:check_error
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] No se pudo iniciar el servicio.
    echo ---------------------------------------------------
    echo 1. Asegurate de que Docker Desktop este ABIERTO.
    echo    (Busca la ballena en los iconos junto al reloj)
    echo 2. Si acaba de instalarse, REINICIA tu PC.
    echo ---------------------------------------------------
    pause
    exit /b
)

echo.
echo [SUCCESS] Servicio Karaoke iniciado correctamente!
echo.
pause

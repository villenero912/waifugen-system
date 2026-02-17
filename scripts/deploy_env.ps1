# ============================================================================
# Script de Despliegue de Variables de Entorno - Sistema WaifuGen (PowerShell)
# ============================================================================
# Este script sube el archivo .env al VPS y reinicia los servicios
# Uso: .\deploy_env.ps1
# ============================================================================

# Configuración de colores
$Host.UI.RawUI.ForegroundColor = "White"

function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-ColorOutput Green "============================================================================"
Write-ColorOutput Green "  Sistema WaifuGen - Despliegue de Configuración"
Write-ColorOutput Green "============================================================================"
Write-Output ""

# ============================================================================
# CONFIGURACIÓN DEL VPS
# ============================================================================
$VPS_IP = "72.61.143.251"  # IP del VPS Hostinger
$VPS_USER = "root"
$VPS_PROJECT_DIR = "/waifugen-system/waifugen_system"
$LOCAL_ENV_FILE = ".env"

# ============================================================================
# PASO 1: Verificar que existe el archivo .env local
# ============================================================================
Write-ColorOutput Yellow "[1/6] Verificando archivo .env local..."
if (-Not (Test-Path $LOCAL_ENV_FILE)) {
    Write-ColorOutput Red "ERROR: No se encuentra el archivo .env"
    Write-Output "Por favor, asegúrate de que el archivo .env existe en el directorio actual"
    exit 1
}
Write-ColorOutput Green "✓ Archivo .env encontrado"
Write-Output ""

# ============================================================================
# PASO 2: Hacer backup del .env actual en el VPS (si existe)
# ============================================================================
Write-ColorOutput Yellow "[2/6] Haciendo backup del .env actual en el VPS..."
$backupCommand = @"
cd /root/waifugen_system
if [ -f .env ]; then
    BACKUP_FILE=".env.backup.`$(date +%Y%m%d_%H%M%S)"
    cp .env "`$BACKUP_FILE"
    echo "✓ Backup creado: `$BACKUP_FILE"
else
    echo "✓ No hay archivo .env previo (primera instalación)"
fi
"@
ssh "$VPS_USER@$VPS_IP" $backupCommand
Write-Output ""

# ============================================================================
# PASO 3: Subir el nuevo archivo .env al VPS
# ============================================================================
Write-ColorOutput Yellow "[3/6] Subiendo nuevo archivo .env al VPS..."
scp "$LOCAL_ENV_FILE" "${VPS_USER}@${VPS_IP}:${VPS_PROJECT_DIR}/.env"
Write-ColorOutput Green "✓ Archivo .env subido correctamente"
Write-Output ""

# ============================================================================
# PASO 4: Establecer permisos seguros
# ============================================================================
Write-ColorOutput Yellow "[4/6] Configurando permisos de seguridad..."
$permissionsCommand = @"
cd /root/waifugen_system
chmod 600 .env
chown root:root .env
echo "✓ Permisos configurados: 600 (solo lectura/escritura para root)"
"@
ssh "$VPS_USER@$VPS_IP" $permissionsCommand
Write-Output ""

# ============================================================================
# PASO 5: Detener y limpiar contenedores actuales
# ============================================================================
Write-ColorOutput Yellow "[5/6] Deteniendo contenedores actuales..."
$stopCommand = @"
cd /root/waifugen_system
echo "Deteniendo todos los contenedores..."
docker-compose down
echo "✓ Contenedores detenidos"
"@
ssh "$VPS_USER@$VPS_IP" $stopCommand
Write-Output ""

# ============================================================================
# PASO 6: Iniciar servicios con la nueva configuración
# ============================================================================
Write-ColorOutput Yellow "[6/6] Iniciando servicios con nueva configuración..."
$startCommand = @"
cd /root/waifugen_system

echo "Verificando configuración de Docker Compose..."
docker-compose config > /dev/null 2>&1
if [ `$? -eq 0 ]; then
    echo "✓ Configuración válida"
else
    echo "✗ ERROR en la configuración de Docker Compose"
    exit 1
fi

echo ""
echo "Iniciando servicios en segundo plano..."
docker-compose up -d

echo ""
echo "Esperando 10 segundos para que los servicios inicien..."
sleep 10

echo ""
echo "Estado de los contenedores:"
docker-compose ps

echo ""
echo "Verificando logs de servicios críticos..."
echo ""
echo "=== Logs de PostgreSQL ==="
docker-compose logs --tail=5 postgres

echo ""
echo "=== Logs de N8N ==="
docker-compose logs --tail=5 n8n

echo ""
echo "=== Logs de Worker ==="
docker-compose logs --tail=5 worker
"@
ssh "$VPS_USER@$VPS_IP" $startCommand

# ============================================================================
# RESUMEN FINAL
# ============================================================================
Write-Output ""
Write-ColorOutput Green "============================================================================"
Write-ColorOutput Green "  ✓ Despliegue Completado"
Write-ColorOutput Green "============================================================================"
Write-Output ""
Write-ColorOutput Yellow "Próximos pasos:"
Write-Output "1. Verificar que todos los contenedores están corriendo:"
Write-Output "   ssh $VPS_USER@$VPS_IP 'cd $VPS_PROJECT_DIR && docker-compose ps'"
Write-Output ""
Write-Output "2. Monitorear logs en tiempo real:"
Write-Output "   ssh $VPS_USER@$VPS_IP 'cd $VPS_PROJECT_DIR && docker-compose logs -f'"
Write-Output ""
Write-Output "3. Acceder a N8N:"
Write-Output "   http://${VPS_IP}:5678"
Write-Output ""
Write-Output "4. Acceder a Grafana:"
Write-Output "   http://${VPS_IP}:3000"
Write-Output "   Usuario: admin"
Write-Output "   Contraseña: Otoñoazul82@Grafana2026"
Write-Output ""
Write-ColorOutput Green "¡Listo para configurar los workflows de N8N!"
Write-Output ""

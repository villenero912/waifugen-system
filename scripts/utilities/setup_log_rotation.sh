#!/bin/bash
# ============================================================================
# Configuración de Rotación Automática de Logs - WaifuGen VPS
# ============================================================================
# Este script configura la rotación automática de logs para prevenir
# que ocupen demasiado espacio en el futuro
# Uso: bash setup_log_rotation.sh
# ============================================================================

echo "============================================================================"
echo "  CONFIGURACIÓN DE ROTACIÓN DE LOGS - WaifuGen VPS"
echo "============================================================================"
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ============================================================================
# 1. CONFIGURAR LÍMITES DE LOGS DE DOCKER
# ============================================================================

echo -e "${YELLOW}🐳 1. Configurando límites de logs de Docker...${NC}"

# Crear o actualizar daemon.json
DOCKER_DAEMON_FILE="/etc/docker/daemon.json"

# Backup del archivo existente si existe
if [ -f "$DOCKER_DAEMON_FILE" ]; then
    cp "$DOCKER_DAEMON_FILE" "$DOCKER_DAEMON_FILE.backup.$(date +%Y%m%d)"
    echo "  → Backup creado: $DOCKER_DAEMON_FILE.backup.$(date +%Y%m%d)"
fi

# Crear configuración de logs
cat > "$DOCKER_DAEMON_FILE" << 'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

echo "  → Configuración de logs de Docker actualizada"
echo "  → Límite: 10MB por archivo, máximo 3 archivos por contenedor"
echo ""

# Reiniciar Docker para aplicar cambios
echo "  → Reiniciando Docker..."
systemctl restart docker

echo -e "${GREEN}✅ Límites de logs de Docker configurados${NC}"
echo ""

# ============================================================================
# 2. CONFIGURAR ROTACIÓN DE LOGS DEL SISTEMA
# ============================================================================

echo -e "${YELLOW}📝 2. Configurando rotación de logs del sistema...${NC}"

# Configurar journald para limitar logs
JOURNALD_CONF="/etc/systemd/journald.conf"

if [ -f "$JOURNALD_CONF" ]; then
    cp "$JOURNALD_CONF" "$JOURNALD_CONF.backup.$(date +%Y%m%d)"
fi

cat > "$JOURNALD_CONF" << 'EOF'
[Journal]
SystemMaxUse=500M
SystemMaxFileSize=100M
RuntimeMaxUse=100M
MaxRetentionSec=7day
EOF

echo "  → Configuración de journald actualizada"
echo "  → Límite: 500MB total, 100MB por archivo, retención 7 días"
echo ""

# Reiniciar journald
systemctl restart systemd-journald

echo -e "${GREEN}✅ Rotación de logs del sistema configurada${NC}"
echo ""

# ============================================================================
# 3. CREAR CRON JOB PARA LIMPIEZA AUTOMÁTICA
# ============================================================================

echo -e "${YELLOW}⏰ 3. Configurando limpieza automática semanal...${NC}"

# Crear script de limpieza semanal
WEEKLY_CLEANUP="/usr/local/bin/waifugen_weekly_cleanup.sh"

cat > "$WEEKLY_CLEANUP" << 'EOF'
#!/bin/bash
# Limpieza automática semanal de WaifuGen

echo "$(date): Iniciando limpieza automática semanal" >> /var/log/waifugen_cleanup.log

# Limpiar Docker
docker system prune -f >> /var/log/waifugen_cleanup.log 2>&1

# Limpiar logs antiguos
journalctl --vacuum-time=7d >> /var/log/waifugen_cleanup.log 2>&1

# Limpiar APT
apt-get clean >> /var/log/waifugen_cleanup.log 2>&1
apt-get autoremove -y >> /var/log/waifugen_cleanup.log 2>&1

echo "$(date): Limpieza completada" >> /var/log/waifugen_cleanup.log
echo "---" >> /var/log/waifugen_cleanup.log
EOF

chmod +x "$WEEKLY_CLEANUP"

# Añadir a crontab (ejecutar cada domingo a las 3 AM)
CRON_JOB="0 3 * * 0 $WEEKLY_CLEANUP"

# Verificar si ya existe el cron job
if ! crontab -l 2>/dev/null | grep -q "$WEEKLY_CLEANUP"; then
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "  → Cron job añadido: Limpieza cada domingo a las 3 AM"
else
    echo "  → Cron job ya existe"
fi

echo -e "${GREEN}✅ Limpieza automática configurada${NC}"
echo ""

# ============================================================================
# RESUMEN
# ============================================================================

echo "============================================================================"
echo -e "${GREEN}✅ CONFIGURACIÓN COMPLETADA${NC}"
echo "============================================================================"
echo ""
echo "Configuraciones aplicadas:"
echo ""
echo "1. 🐳 Docker Logs:"
echo "   - Máximo 10MB por archivo de log"
echo "   - Máximo 3 archivos por contenedor"
echo "   - Total máximo: ~30MB por contenedor"
echo ""
echo "2. 📝 System Logs (journald):"
echo "   - Máximo 500MB total"
echo "   - Máximo 100MB por archivo"
echo "   - Retención: 7 días"
echo ""
echo "3. ⏰ Limpieza Automática:"
echo "   - Frecuencia: Cada domingo a las 3 AM"
echo "   - Log: /var/log/waifugen_cleanup.log"
echo ""
echo "NOTA: Los contenedores existentes mantendrán su configuración actual."
echo "      Recrea los contenedores para aplicar los nuevos límites:"
echo "      docker-compose down && docker-compose up -d"
echo ""
echo "============================================================================"

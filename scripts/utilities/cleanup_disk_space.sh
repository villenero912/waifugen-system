#!/bin/bash
# ============================================================================
# Script de Limpieza de Espacio en Disco - WaifuGen VPS
# ============================================================================
# Este script libera espacio en el servidor de forma segura
# Uso: bash cleanup_disk_space.sh
# ============================================================================

set -e  # Salir si hay error

echo "============================================================================"
echo "  LIMPIEZA DE ESPACIO EN DISCO - WaifuGen VPS"
echo "============================================================================"
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Función para mostrar espacio antes y después
show_space() {
    df -h / | grep -v Filesystem
}

echo -e "${YELLOW}📊 Espacio ANTES de la limpieza:${NC}"
BEFORE=$(show_space)
echo "$BEFORE"
echo ""

# ============================================================================
# 1. LIMPIEZA DE DOCKER
# ============================================================================

echo -e "${YELLOW}🐳 1. Limpiando Docker...${NC}"
echo "============================================================================"

echo "  → Eliminando contenedores detenidos..."
docker container prune -f

echo "  → Eliminando imágenes no utilizadas..."
docker image prune -a -f

echo "  → Eliminando volúmenes huérfanos..."
docker volume prune -f

echo "  → Eliminando redes no utilizadas..."
docker network prune -f

echo "  → Limpiando build cache..."
docker builder prune -a -f

echo -e "${GREEN}✅ Docker limpiado${NC}"
echo ""

# ============================================================================
# 2. LIMPIEZA DE LOGS DE DOCKER
# ============================================================================

echo -e "${YELLOW}📝 2. Limpiando logs de Docker...${NC}"
echo "============================================================================"

# Truncar logs de contenedores que sean mayores a 100MB
find /var/lib/docker/containers -name "*-json.log" -size +100M -exec sh -c 'echo "Truncando: $1"; truncate -s 0 "$1"' _ {} \;

echo -e "${GREEN}✅ Logs de Docker limpiados${NC}"
echo ""

# ============================================================================
# 3. LIMPIEZA DEL SISTEMA
# ============================================================================

echo -e "${YELLOW}🗑️  3. Limpiando sistema...${NC}"
echo "============================================================================"

echo "  → Limpiando caché de APT..."
apt-get clean
apt-get autoclean

echo "  → Eliminando paquetes huérfanos..."
apt-get autoremove -y

echo "  → Limpiando logs antiguos del sistema..."
journalctl --vacuum-time=7d
journalctl --vacuum-size=100M

echo "  → Limpiando archivos temporales..."
rm -rf /tmp/*
rm -rf /var/tmp/*

echo -e "${GREEN}✅ Sistema limpiado${NC}"
echo ""

# ============================================================================
# 4. LIMPIEZA ESPECÍFICA DE WAIFUGEN (OPCIONAL)
# ============================================================================

echo -e "${YELLOW}🎨 4. Limpiando archivos temporales de WaifuGen...${NC}"
echo "============================================================================"

if [ -d "/root/waifugen_system" ]; then
    # Limpiar archivos temporales de generación
    find /root/waifugen_system -name "*.tmp" -delete 2>/dev/null || true
    find /root/waifugen_system -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find /root/waifugen_system -name "*.pyc" -delete 2>/dev/null || true
    
    echo -e "${GREEN}✅ Archivos temporales de WaifuGen limpiados${NC}"
else
    echo "  → Directorio WaifuGen no encontrado, saltando..."
fi
echo ""

# ============================================================================
# RESUMEN
# ============================================================================

echo "============================================================================"
echo -e "${GREEN}✅ LIMPIEZA COMPLETADA${NC}"
echo "============================================================================"
echo ""

echo -e "${YELLOW}📊 Espacio DESPUÉS de la limpieza:${NC}"
AFTER=$(show_space)
echo "$AFTER"
echo ""

echo -e "${YELLOW}📈 Comparación:${NC}"
echo "Antes:  $BEFORE"
echo "Después: $AFTER"
echo ""

echo -e "${GREEN}Próximos pasos recomendados:${NC}"
echo "  1. Configura rotación automática de logs (ver setup_log_rotation.sh)"
echo "  2. Monitorea el espacio regularmente"
echo "  3. Considera aumentar el disco si es necesario"
echo ""
echo "============================================================================"

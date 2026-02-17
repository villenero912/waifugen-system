#!/bin/bash
# ============================================================================
# Script de Análisis de Espacio en Disco - WaifuGen VPS
# ============================================================================
# Este script analiza qué está ocupando espacio en el servidor
# Uso: bash analyze_disk_usage.sh
# ============================================================================

echo "============================================================================"
echo "  ANÁLISIS DE ESPACIO EN DISCO - WaifuGen VPS"
echo "============================================================================"
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}📊 1. Uso General del Disco${NC}"
echo "============================================================================"
df -h
echo ""

echo -e "${YELLOW}📁 2. Top 10 Directorios Más Grandes (Raíz)${NC}"
echo "============================================================================"
du -h --max-depth=1 / 2>/dev/null | sort -hr | head -n 10
echo ""

echo -e "${YELLOW}🐳 3. Espacio Usado por Docker${NC}"
echo "============================================================================"
docker system df
echo ""

echo -e "${YELLOW}📦 4. Imágenes Docker${NC}"
echo "============================================================================"
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
echo ""

echo -e "${YELLOW}🗑️  5. Contenedores Detenidos${NC}"
echo "============================================================================"
docker ps -a --filter "status=exited" --format "table {{.Names}}\t{{.Status}}\t{{.Size}}"
echo ""

echo -e "${YELLOW}💾 6. Volúmenes Docker${NC}"
echo "============================================================================"
docker volume ls
echo ""
docker system df -v | grep -A 20 "Local Volumes"
echo ""

echo -e "${YELLOW}📝 7. Logs de Docker (Top 10 más grandes)${NC}"
echo "============================================================================"
find /var/lib/docker/containers -name "*-json.log" -exec ls -lh {} \; 2>/dev/null | sort -k5 -hr | head -n 10
echo ""

echo -e "${YELLOW}📂 8. Directorio del Proyecto WaifuGen${NC}"
echo "============================================================================"
if [ -d "/root/waifugen_system" ]; then
    du -h --max-depth=2 /root/waifugen_system | sort -hr | head -n 15
else
    echo "Directorio /root/waifugen_system no encontrado"
fi
echo ""

echo -e "${YELLOW}🗂️  9. Logs del Sistema${NC}"
echo "============================================================================"
du -sh /var/log/* 2>/dev/null | sort -hr | head -n 10
echo ""

echo -e "${YELLOW}📊 10. Resumen de Espacio Potencialmente Recuperable${NC}"
echo "============================================================================"

# Calcular espacio recuperable
DOCKER_UNUSED=$(docker system df --format "{{.Reclaimable}}" | grep -v "SIZE" | head -n 1)
STOPPED_CONTAINERS=$(docker ps -a --filter "status=exited" -q | wc -l)
DANGLING_IMAGES=$(docker images -f "dangling=true" -q | wc -l)
UNUSED_VOLUMES=$(docker volume ls -f "dangling=true" -q | wc -l)

echo -e "${GREEN}Docker:${NC}"
echo "  - Espacio recuperable total: $DOCKER_UNUSED"
echo "  - Contenedores detenidos: $STOPPED_CONTAINERS"
echo "  - Imágenes huérfanas: $DANGLING_IMAGES"
echo "  - Volúmenes no utilizados: $UNUSED_VOLUMES"
echo ""

# Tamaño de logs
LOG_SIZE=$(du -sh /var/log 2>/dev/null | cut -f1)
echo -e "${GREEN}Sistema:${NC}"
echo "  - Logs del sistema: $LOG_SIZE"
echo ""

echo "============================================================================"
echo -e "${GREEN}✅ Análisis completado${NC}"
echo ""
echo -e "${YELLOW}Próximos pasos:${NC}"
echo "  1. Revisa el análisis anterior"
echo "  2. Ejecuta: bash cleanup_disk_space.sh (para limpiar automáticamente)"
echo "  3. O ejecuta comandos específicos de limpieza manual"
echo "============================================================================"

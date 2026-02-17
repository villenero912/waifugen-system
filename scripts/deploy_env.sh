#!/bin/bash
# ============================================================================
# Script de Despliegue de Variables de Entorno - Sistema WaifuGen
# ============================================================================
# Este script sube el archivo .env al VPS y reinicia los servicios
# ============================================================================

set -e  # Salir si hay algún error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # Sin color

echo -e "${GREEN}============================================================================${NC}"
echo -e "${GREEN}  Sistema WaifuGen - Despliegue de Configuración${NC}"
echo -e "${GREEN}============================================================================${NC}"
echo ""

# ============================================================================
# CONFIGURACIÓN DEL VPS
# ============================================================================
VPS_IP="165.254.0.1"  # Cambiar por tu IP real del VPS
VPS_USER="root"
VPS_PROJECT_DIR="/root/waifugen_system"
LOCAL_ENV_FILE=".env"

# ============================================================================
# PASO 1: Verificar que existe el archivo .env local
# ============================================================================
echo -e "${YELLOW}[1/6] Verificando archivo .env local...${NC}"
if [ ! -f "$LOCAL_ENV_FILE" ]; then
    echo -e "${RED}ERROR: No se encuentra el archivo .env${NC}"
    echo "Por favor, asegúrate de que el archivo .env existe en el directorio actual"
    exit 1
fi
echo -e "${GREEN}✓ Archivo .env encontrado${NC}"
echo ""

# ============================================================================
# PASO 2: Hacer backup del .env actual en el VPS (si existe)
# ============================================================================
echo -e "${YELLOW}[2/6] Haciendo backup del .env actual en el VPS...${NC}"
ssh ${VPS_USER}@${VPS_IP} << 'ENDSSH'
cd /root/waifugen_system
if [ -f .env ]; then
    BACKUP_FILE=".env.backup.$(date +%Y%m%d_%H%M%S)"
    cp .env "$BACKUP_FILE"
    echo "✓ Backup creado: $BACKUP_FILE"
else
    echo "✓ No hay archivo .env previo (primera instalación)"
fi
ENDSSH
echo ""

# ============================================================================
# PASO 3: Subir el nuevo archivo .env al VPS
# ============================================================================
echo -e "${YELLOW}[3/6] Subiendo nuevo archivo .env al VPS...${NC}"
scp "$LOCAL_ENV_FILE" ${VPS_USER}@${VPS_IP}:${VPS_PROJECT_DIR}/.env
echo -e "${GREEN}✓ Archivo .env subido correctamente${NC}"
echo ""

# ============================================================================
# PASO 4: Establecer permisos seguros
# ============================================================================
echo -e "${YELLOW}[4/6] Configurando permisos de seguridad...${NC}"
ssh ${VPS_USER}@${VPS_IP} << 'ENDSSH'
cd /root/waifugen_system
chmod 600 .env
chown root:root .env
echo "✓ Permisos configurados: 600 (solo lectura/escritura para root)"
ENDSSH
echo ""

# ============================================================================
# PASO 5: Detener y limpiar contenedores actuales
# ============================================================================
echo -e "${YELLOW}[5/6] Deteniendo contenedores actuales...${NC}"
ssh ${VPS_USER}@${VPS_IP} << 'ENDSSH'
cd /root/waifugen_system
echo "Deteniendo todos los contenedores..."
docker-compose down
echo "✓ Contenedores detenidos"
ENDSSH
echo ""

# ============================================================================
# PASO 6: Iniciar servicios con la nueva configuración
# ============================================================================
echo -e "${YELLOW}[6/6] Iniciando servicios con nueva configuración...${NC}"
ssh ${VPS_USER}@${VPS_IP} << 'ENDSSH'
cd /root/waifugen_system

echo "Verificando configuración de Docker Compose..."
docker-compose config > /dev/null 2>&1
if [ $? -eq 0 ]; then
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

ENDSSH

# ============================================================================
# RESUMEN FINAL
# ============================================================================
echo ""
echo -e "${GREEN}============================================================================${NC}"
echo -e "${GREEN}  ✓ Despliegue Completado${NC}"
echo -e "${GREEN}============================================================================${NC}"
echo ""
echo -e "${YELLOW}Próximos pasos:${NC}"
echo "1. Verificar que todos los contenedores están corriendo:"
echo "   ssh ${VPS_USER}@${VPS_IP} 'cd ${VPS_PROJECT_DIR} && docker-compose ps'"
echo ""
echo "2. Monitorear logs en tiempo real:"
echo "   ssh ${VPS_USER}@${VPS_IP} 'cd ${VPS_PROJECT_DIR} && docker-compose logs -f'"
echo ""
echo "3. Acceder a N8N:"
echo "   http://${VPS_IP}:5678"
echo ""
echo "4. Acceder a Grafana:"
echo "   http://${VPS_IP}:3000"
echo "   Usuario: admin"
echo "   Contraseña: Otoñoazul82@Grafana2026"
echo ""
echo -e "${GREEN}¡Listo para configurar los workflows de N8N!${NC}"
echo ""

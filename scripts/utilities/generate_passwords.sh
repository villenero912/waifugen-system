#!/bin/bash
# ============================================================================
# Generador de Contraseñas Seguras - Sistema WaifuGen (Bash)
# ============================================================================
# Script wrapper para ejecutar el generador de contraseñas Python
# ============================================================================

set -e

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Contraseña maestra por defecto
MASTER_PASSWORD="${1:-Otoñoazul82@}"
OUTPUT_FILE="${2:-.env}"

echo -e "${GREEN}============================================================================${NC}"
echo -e "${GREEN}  Generador de Contraseñas Seguras - WaifuGen System${NC}"
echo -e "${GREEN}============================================================================${NC}"
echo ""

# Verificar que Python está instalado
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: Python 3 no está instalado${NC}"
    echo "Por favor, instala Python 3 para continuar"
    exit 1
fi

echo -e "${YELLOW}Contraseña maestra:${NC} $MASTER_PASSWORD"
echo -e "${YELLOW}Archivo de salida:${NC} $OUTPUT_FILE"
echo ""

# Ejecutar el generador de contraseñas Python
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/generate_passwords.py" --master "$MASTER_PASSWORD" --output "$OUTPUT_FILE"

echo ""
echo -e "${GREEN}✅ Contraseñas generadas exitosamente${NC}"
echo ""
echo -e "${YELLOW}Próximos pasos:${NC}"
echo "1. Edita el archivo $OUTPUT_FILE y añade tus claves API"
echo "2. Establece permisos seguros: chmod 600 $OUTPUT_FILE"
echo "3. Despliega al VPS usando: ./scripts/deploy_env.sh"
echo ""

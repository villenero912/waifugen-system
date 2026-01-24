#!/bin/bash

###############################################################################
# PRIMERA PRUEBA END-TO-END - Generación de Reel Completo
# WaifuGen System - Pipeline Test
###############################################################################

set -e

echo "==========================================="
echo "WaifuGen - Test Pipeline Completo"
echo "==========================================="
echo ""

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Crear directorio de pruebas
TEST_DIR="/tmp/waifugen_test_$(date +%Y%m%d_%H%M%S)"
mkdir -p $TEST_DIR
cd $TEST_DIR

echo -e "${YELLOW}Directorio de pruebas: $TEST_DIR${NC}"
echo ""

###############################################################################
# PASO 1: Probar Ollama (Generación de Prompt)
###############################################################################

echo "=========================================="
echo "PASO 1: Generando prompt con Ollama"
echo "=========================================="

PROMPT_REQUEST="Generate a creative 30-word prompt for a TikTok reel featuring Miyuki Sakura, a 22-year-old Japanese woman. Theme: morning motivation. Style: energetic and positive."

echo "Enviando request a Ollama..."
GENERATED_PROMPT=$(docker exec -i waifugen_ollama ollama run llama3 "$PROMPT_REQUEST" 2>/dev/null | head -n 5 | tr '\n' ' ')

if [ -z "$GENERATED_PROMPT" ]; then
    echo -e "${RED}ERROR: Ollama no generó prompt${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prompt generado:${NC}"
echo "$GENERATED_PROMPT"
echo ""

# Guardar prompt
echo "$GENERATED_PROMPT" > prompt.txt

###############################################################################
# PASO 2: Probar Piper TTS (Generación de Voz)
###############################################################################

echo "=========================================="
echo "PASO 2: Generando voz con Piper TTS"
echo "=========================================="

VOICE_SCRIPT="Hello! I am Miyuki Sakura. Today is a beautiful day full of possibilities. Let's make it amazing together!"

echo "Generando audio..."
echo "$VOICE_SCRIPT" | docker exec -i waifugen_piper piper \
    --model en_US-amy-medium \
    --output_file /tmp/voice.wav

# Copiar audio del contenedor
docker cp waifugen_piper:/tmp/voice.wav voice.wav

if [ -f "voice.wav" ]; then
    echo -e "${GREEN}✓ Voz generada: voice.wav${NC}"
    ls -lh voice.wav
else
    echo -e "${RED}ERROR: No se generó el archivo de voz${NC}"
    exit 1
fi

echo ""

###############################################################################
# PASO 3: Simular A2E (Nota: requiere API key real)
###############################################################################

echo "=========================================="
echo "PASO 3: Test A2E API Connection"
echo "=========================================="

# Verificar que la API key existe
if [ -z "$A2E_API_KEY" ]; then
    echo -e "${YELLOW}⚠ A2E_API_KEY no configurada en environment${NC}"
    echo -e "${YELLOW}⚠ Saltando generación de video real${NC}"
    echo -e "${YELLOW}⚠ Usando placeholder para continuar test${NC}"
    
    # Crear archivo placeholder
    touch video_placeholder.mp4
    echo "Este sería el video generado por A2E" > video_info.txt
else
    echo "API Key detectada, preparando request A2E..."
    echo "Prompt: $GENERATED_PROMPT"
    echo ""
    echo -e "${YELLOW}Nota: Para test completo, ejecuta el script Python de A2E${NC}"
    echo -e "${YELLOW}python3 /app/src/api/a2e_client.py${NC}"
fi

echo ""

###############################################################################
# PASO 4: Música de Fondo (Placeholder)
###############################################################################

echo "=========================================="
echo "PASO 4: Música de fondo"
echo "=========================================="

echo -e "${YELLOW}⚠ Usando música placeholder${NC}"
echo "En producción: Replicate MusicGen o Pixabay API"

# Crear archivo info
echo "Música: Lo-fi beat, 30 segundos" > music_info.txt

echo ""

###############################################################################
# PASO 5: Verificar FFmpeg
###############################################################################

echo "=========================================="
echo "PASO 5: Verificando FFmpeg"
echo "=========================================="

if command -v ffmpeg &> /dev/null; then
    echo -e "${GREEN}✓ FFmpeg instalado${NC}"
    ffmpeg -version | head -n 1
else
    echo -e "${RED}ERROR: FFmpeg no encontrado${NC}"
    echo "Instalando FFmpeg..."
    apt-get update && apt-get install -y ffmpeg
fi

echo ""

###############################################################################
# RESUMEN
###############################################################################

echo "==========================================="
echo "RESUMEN DEL TEST"
echo "==========================================="
echo ""
echo -e "${GREEN}✓ Ollama (LLM):${NC} Funcionando - Prompt generado"
echo -e "${GREEN}✓ Piper TTS:${NC} Funcionando - Voz generada"
echo -e "${YELLOW}⚠ A2E API:${NC} Pendiente API key en environment"
echo -e "${YELLOW}⚠ Música:${NC} Placeholder (Replicate/Pixabay en producción)"
echo -e "${GREEN}✓ FFmpeg:${NC} Disponible"
echo ""
echo "Archivos generados en: $TEST_DIR"
ls -lh

echo ""
echo "==========================================="
echo "PRÓXIMOS PASOS"
echo "==========================================="
echo ""
echo "1. Configurar A2E_API_KEY en .env:"
echo "   A2E_API_KEY=sk_eyJhbGc..."
echo ""
echo "2. Reiniciar servicios:"
echo "   docker compose restart app worker"
echo ""
echo "3. Ejecutar test completo con A2E:"
echo "   python3 test_full_reel_generation.py"
echo ""
echo "4. Verificar costo de créditos A2E"
echo ""

exit 0

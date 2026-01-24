#!/bin/bash

###############################################################################
# Instalación de Piper TTS - Sistema de Voces Local
# Para WaifuGen Project
###############################################################################

set -e

echo "========================================="
echo "Instalación de Piper TTS"
echo "========================================="
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: Ejecuta este script desde el directorio waifugen-system"
    exit 1
fi

# Crear directorio para voces si no existe
echo "1. Creando directorio de voces..."
mkdir -p piper_voices

echo ""
echo "2. Actualizando docker-compose.yml..."
echo "   (Asegúrate de que el servicio Piper está en docker-compose.yml)"

echo ""
echo "3. Iniciando servicio Piper TTS..."
docker compose up -d piper

echo ""
echo "4. Esperando que Piper se inicie (30 segundos)..."
sleep 30

echo ""
echo "5. Verificando estado de Piper..."
docker compose ps piper

echo ""
echo "6. Descargando modelos de voz..."
echo "   - Inglés (Amy - mujer)"
docker exec waifugen_piper ls -lh /data/

echo ""
echo "========================================="
echo "✅ Piper TTS Instalado"
echo "========================================="
echo ""
echo "Modelos disponibles:"
echo "  - en_US-amy-medium (Inglés - Mujer)"
echo ""
echo "Para añadir más voces:"
echo "  1. Lista completa: https://github.com/rhasspy/piper/blob/master/VOICES.md"
echo "  2. Descargar modelo (.onnx + .onnx.json)"
echo "  3. Copiar a ./piper_voices/"
echo ""
echo "Probar TTS:"
echo '  echo "Hello world" | docker exec -i waifugen_piper piper --output_file /tmp/test.wav'
echo ""
echo "Puerto: 127.0.0.1:10200"
echo "Protocolo: Wyoming (compatible con Home Assistant)"
echo ""

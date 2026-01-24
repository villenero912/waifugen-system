#!/bin/bash

###############################################################################
# Configuración de Ollama - Descarga de Modelos para WaifuGen
# Este script descarga los modelos LLM necesarios para el proyecto
###############################################################################

echo "========================================="
echo "Configurando Ollama para WaifuGen"
echo "========================================="
echo ""

# Verificar que Ollama está corriendo
echo "1. Verificando estado de Ollama..."
docker exec waifugen_ollama ollama list

echo ""
echo "2. Descargando llama3 (modelo principal)..."
docker exec waifugen_ollama ollama pull llama3

echo ""
echo "3. Descargando mistral (modelo alternativo rápido)..."
docker exec waifugen_ollama ollama pull mistral

echo ""
echo "4. Verificando modelos instalados..."
docker exec waifugen_ollama ollama list

echo ""
echo "========================================="
echo "✅ Configuración de Ollama completa"
echo "========================================="
echo ""
echo "Modelos disponibles:"
echo "  - llama3: Modelo principal (mejor para todo)"
echo "  - mistral: Modelo rápido (alternativa)"
echo ""
echo "Uso de memoria estimado:"
echo "  - llama3: ~4.7 GB"
echo "  - mistral: ~4.1 GB"
echo ""
echo "Próximo paso: Probar generación de texto"

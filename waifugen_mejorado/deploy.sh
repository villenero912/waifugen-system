#!/bin/bash

# Script de despliegue automatizado para WaifuGen v2
# Este script sube el paquete corregido a un servidor remoto, lo configura e instala las dependencias.

# --- Configuración Local ---
LOCAL_ZIP_FILE="/home/ubuntu/waifugen_v2_corrected.zip"
LOCAL_ENV_FILE="/home/ubuntu/waifugen_v2/.env"

# --- Variables del Servidor Remoto ---
REMOTE_USER=""
REMOTE_HOST=""
REMOTE_PATH="/home/${REMOTE_USER}/waifugen_v2"

# --- Funciones de Utilidad ---
function read_input() {
    local __resultvar=$1
    local __prompt=$2
    local __default=$3
    
    read -p "${__prompt} [${__default}]: " __input
    local __value=${__input:-${__default}}
    eval $__resultvar="'${__value}'"
}

function check_prerequisites() {
    echo "Verificando prerrequisitos locales..."
    if [ ! -f "$LOCAL_ZIP_FILE" ]; then
        echo "Error: El archivo ZIP corregido no se encuentra en $LOCAL_ZIP_FILE"
        echo "Asegúrate de que 'waifugen_v2_corrected.zip' existe en la ruta especificada."
        exit 1
    fi
    if ! command -v ssh &> /dev/null; then
        echo "Error: SSH no está instalado. Por favor, instala OpenSSH client."
        exit 1
    fi
    if ! command -v scp &> /dev/null; then
        echo "Error: SCP no está instalado. Por favor, instala OpenSSH client."
        exit 1
    fi
    echo "Prerrequisitos locales verificados."
}

function get_remote_details() {
    echo "\n--- Detalles del Servidor Remoto ---"
    read_input REMOTE_USER "Usuario SSH del servidor remoto" "ubuntu"
    read_input REMOTE_HOST "Dirección IP o Hostname del servidor remoto" "your_server_ip"
    REMOTE_PATH="/home/${REMOTE_USER}/waifugen_v2"
    echo "La ruta de despliegue en el servidor remoto será: ${REMOTE_PATH}"
}

function get_env_vars() {
    echo "\n--- Configuración de Variables de Entorno ---"
    read -s -p "Introduce la ENCRYPTION_KEY para el archivo .env (no se mostrará): " ENCRYPTION_KEY
    echo
    if [ -z "$ENCRYPTION_KEY" ]; then
        echo "Advertencia: ENCRYPTION_KEY no puede estar vacía. Usando un valor por defecto para desarrollo."
        ENCRYPTION_KEY="test_encryption_key_for_development_only_12345"
    fi
    
    read -s -p "Introduce la clave de la API de OpenAI (opcional, no se mostrará): " OPENAI_API_KEY
    echo
    read -s -p "Introduce la clave de la API de Google (opcional, no se mostrará): " GOOGLE_API_KEY
    echo
    read -s -p "Introduce la clave de la API de Telegram Bot (opcional, no se mostrará): " TELEGRAM_BOT_TOKEN
    echo
    read -s -p "Introduce el ID del chat de Telegram (opcional, no se mostrará): " TELEGRAM_CHAT_ID
    echo
    
    # Phase 2 Variables
    read -p "Introduce el ENCRYPTION_SALT (dejalo vacío para generar uno nuevo): " ENCRYPTION_SALT
    read -s -p "Introduce GUMROAD_ACCESS_TOKEN (opcional): " GUMROAD_ACCESS_TOKEN
    echo
    read -s -p "Introduce PATREON_ACCESS_TOKEN (opcional): " PATREON_ACCESS_TOKEN
    echo
    read -p "Introduce PATREON_CAMPAIGN_ID (opcional): " PATREON_CAMPAIGN_ID
}

function upload_and_configure() {
    echo "\n--- Subiendo y configurando el sistema en el servidor remoto ---"
    
    # 1. Subir el archivo ZIP
    echo "Subiendo $LOCAL_ZIP_FILE a ${REMOTE_USER}@${REMOTE_HOST}:/tmp/ ..."
    scp "$LOCAL_ZIP_FILE" "${REMOTE_USER}@${REMOTE_HOST}:/tmp/waifugen_v2_corrected.zip"
    if [ $? -ne 0 ]; then
        echo "Error: Falló la subida del archivo ZIP. Abortando."
        exit 1
    fi
    echo "Archivo ZIP subido exitosamente."
    
    # 2. Ejecutar comandos en el servidor remoto
    echo "Ejecutando comandos de configuración en ${REMOTE_HOST}..."
    ssh "${REMOTE_USER}@${REMOTE_HOST}" << EOF
        set -e # Salir inmediatamente si un comando falla
        
        echo "Creando directorio de destino: ${REMOTE_PATH}"
        mkdir -p "${REMOTE_PATH}"
        
        echo "Descomprimiendo el archivo ZIP..."
        unzip -o /tmp/waifugen_v2_corrected.zip -d "${REMOTE_PATH}/../"
        
        echo "Navegando al directorio del proyecto..."
        cd "${REMOTE_PATH}"
        
        echo "Creando/actualizando archivo .env..."
        cat > .env << EOL
ENCRYPTION_KEY=${ENCRYPTION_KEY}
OPENAI_API_KEY=${OPENAI_API_KEY}
GOOGLE_API_KEY=${GOOGLE_API_KEY}
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID}
# Phase 2 & Security
ENCRYPTION_SALT=${ENCRYPTION_SALT:-"g6Z7v9_L2Wn3P8q1R5t0X4v7B9m1K4j0S2f5G8h3D6k="}
GUMROAD_ACCESS_TOKEN=${GUMROAD_ACCESS_TOKEN}
PATREON_ACCESS_TOKEN=${PATREON_ACCESS_TOKEN}
PATREON_CAMPAIGN_ID=${PATREON_CAMPAIGN_ID}
# Añade aquí otras variables de entorno si son necesarias
EOL
        
        echo "Instalando dependencias del sistema (ffmpeg, etc.)..."
        sudo apt-get update -qq > /dev/null
        sudo apt-get install -y ffmpeg python3-pip > /dev/null
        
        echo "Instalando dependencias de Python..."
        sudo pip3 install -r requirements.txt
        
        echo "Ejecutando despliegue con Docker Compose..."
        docker-compose up -d --build
        
        echo "\n--- Configuración Completa ---"
        echo "El sistema WaifuGen v2 ha sido desplegado en contenedores Docker."
        echo "Puedes ver los logs con: docker-compose logs -f waifugen_app"
        echo "Asegúrate de que todos los servicios externos (ComfyUI, etc.) estén accesibles."
        
        rm /tmp/waifugen_v2_corrected.zip # Limpiar el archivo ZIP temporal
EOF
    if [ $? -ne 0 ]; then
        echo "Error: Falló la ejecución de comandos remotos. Abortando."
        exit 1
    fi
    echo "Configuración remota completada exitosamente."
}

# --- Ejecución Principal ---
check_prerequisites
get_remote_details
get_env_vars
upload_and_configure

echo "\nDespliegue finalizado. Revisa la salida para cualquier error."

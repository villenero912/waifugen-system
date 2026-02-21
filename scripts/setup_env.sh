#!/bin/bash
# ============================================================
# WaifuGen — Configuración Segura de API Keys
# Pide las claves por teclado sin mostrarlas en pantalla
# ============================================================
set -euo pipefail

ENV_FILE="/app/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Ejecuta primero: sudo ./docker/deploy_secure.sh"
    exit 1
fi

echo ""
echo "🔐 CONFIGURACIÓN DE API KEYS"
echo "============================="
echo "Las claves no se mostrarán en pantalla."
echo ""

read_secret() {
    local prompt="$1"
    local var_name="$2"
    local -s value
    read -s -p "$prompt: " value
    echo ""
    if [ -n "$value" ]; then
        sed -i "s|^${var_name}=.*|${var_name}=${value}|" "$ENV_FILE"
        echo "   ✅ $var_name configurado"
    else
        echo "   ⏭  $var_name omitido"
    fi
}

echo "── A2E (Video Generation) ──"
read_secret "A2E_API_KEY" "A2E_API_KEY"
read_secret "A2E_API_ID" "A2E_API_ID"

echo ""
echo "── Replicate (Música) ──"
read_secret "REPLICATE_API_TOKEN" "REPLICATE_API_TOKEN"

echo ""
echo "── Telegram ──"
read_secret "TELEGRAM_BOT_TOKEN" "TELEGRAM_BOT_TOKEN"
read_secret "TELEGRAM_ADMIN_CHAT_ID" "TELEGRAM_ADMIN_CHAT_ID"

echo ""
echo "── Proxies IPRoyal ──"
read_secret "IPROYAL_USERNAME" "IPROYAL_USERNAME"
read_secret "IPROYAL_PASSWORD" "IPROYAL_PASSWORD"

echo ""
echo "── Plataformas Sociales ──"
read_secret "TIKTOK_CLIENT_KEY" "TIKTOK_CLIENT_KEY"
read_secret "TIKTOK_CLIENT_SECRET" "TIKTOK_CLIENT_SECRET"
read_secret "INSTAGRAM_ACCESS_TOKEN" "INSTAGRAM_ACCESS_TOKEN"
read_secret "YOUTUBE_REFRESH_TOKEN" "YOUTUBE_REFRESH_TOKEN"
read_secret "LINE_CHANNEL_ACCESS_TOKEN" "LINE_CHANNEL_ACCESS_TOKEN"
read_secret "NICONICO_CLIENT_ID" "NICONICO_CLIENT_ID"

chmod 600 "$ENV_FILE"
echo ""
echo "✅ Configuración completada."
echo "   Reinicia los servicios: docker-compose -f docker/docker-compose.yml up -d"

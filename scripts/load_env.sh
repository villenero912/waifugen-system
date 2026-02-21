#!/bin/bash
# ============================================================
# WaifuGen — Cargador de variables de entorno
# Source este archivo antes de usar cualquier script
# ============================================================

ENV_FILE="${ENV_FILE:-/app/.env}"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ .env no encontrado en $ENV_FILE"
    exit 1
fi

set -a
source "$ENV_FILE"
set +a

echo "✅ Variables cargadas desde $ENV_FILE"

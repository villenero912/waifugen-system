#!/bin/bash
# ============================================================
# WaifuGen — Setup inicial del VPS
# Ejecutar UNA sola vez después de contratar el servidor
# ============================================================
set -euo pipefail

echo "🚀 WaifuGen VPS Setup"
echo "====================="

# ── Sistema ──────────────────────────────────────────────
apt-get update -qq
apt-get install -y -qq \
    curl wget git unzip \
    ffmpeg \
    openssl \
    ufw \
    fail2ban \
    htop

# ── Docker ───────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
    echo "📦 Instalando Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
fi

if ! command -v docker-compose &>/dev/null; then
    echo "📦 Instalando Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
        -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# ── Firewall ─────────────────────────────────────────────
echo "🔒 Configurando firewall..."
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# ── Fail2ban ─────────────────────────────────────────────
systemctl enable fail2ban
systemctl start fail2ban

# ── Estructura de directorios ─────────────────────────────
echo "📁 Creando estructura..."
mkdir -p /app/{assets/{videos,audio,thumbnails,output},config,logs,reports,voices,ssl}
mkdir -p /app/docker/ssl
chmod 700 /app/docker/ssl

# ── SSL autofirmado (reemplazar por Let's Encrypt en producción) ──
if [ ! -f /app/docker/ssl/cert.pem ]; then
    echo "🔐 Generando certificado SSL autofirmado..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /app/docker/ssl/key.pem \
        -out /app/docker/ssl/cert.pem \
        -subj "/C=JP/ST=Tokyo/L=Tokyo/O=WaifuGen/CN=localhost"
    chmod 600 /app/docker/ssl/key.pem
fi

echo ""
echo "✅ Setup completo."
echo "   Siguiente paso: cd /app && sudo ./docker/deploy_secure.sh"

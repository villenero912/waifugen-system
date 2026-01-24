#!/bin/bash
# =============================================================================
# ELITE 8 System - Automated VPS Setup Script
# =============================================================================
# This script prepares a clean Ubuntu VPS for the WaifuGen System.
# Usage: curl -sSL https://raw.githubusercontent.com/villenero912/waifugen-system/main/scripts/setup_vps.sh | bash
# =============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}>>> Starting ELITE 8 System Setup...${NC}"

# 1. Update System
echo -e "${GREEN}1/5 Updating system packages...${NC}"
sudo apt-get update && sudo apt-get upgrade -y

# 2. Install Docker
if ! command -v docker &> /dev/null; then
    echo -e "${GREEN}2/5 Installing Docker...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
else
    echo -e "${GREEN}2/5 Docker already installed.${NC}"
fi

# 3. Install Docker Compose
if ! command -v docker compose &> /dev/null; then
    echo -e "${GREEN}3/5 Installing Docker Compose...${NC}"
    sudo apt-get install -y docker-compose-plugin
else
    echo -e "${GREEN}3/5 Docker Compose already installed.${NC}"
fi

# 4. Clone Repository
echo -e "${GREEN}4/5 Cloning Repository...${NC}"
if [ ! -d "waifugen-system" ]; then
    git clone https://github.com/villenero912/waifugen-system.git
    cd waifugen-system
else
    cd waifugen-system
    git pull
fi

# 5. Prepare Environment
echo -e "${GREEN}5/5 Preparing environment...${NC}"
if [ ! -f ".env" ]; then
    cp config/.env.example .env
    echo -e "${BLUE}>>> Created .env file from template.${NC}"
    echo -e "${BLUE}>>> IMPORTANT: You must edit the .env file with your API keys!${NC}"
fi

echo -e "${BLUE}============================================================${NC}"
echo -e "${GREEN}SETUP COMPLETE!${NC}"
echo -e "${BLUE}Next steps:${NC}"
echo -e "1. cd waifugen-system"
echo -e "2. nano .env  # Add your API keys"
echo -e "3. docker compose up -d"
echo -e "4. Access n8n at http://$(curl -s ifconfig.me):5678"
echo -e "${BLUE}============================================================${NC}"

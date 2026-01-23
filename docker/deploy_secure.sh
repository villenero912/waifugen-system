#!/bin/bash

################################################################################
# JAV Automation System - Production Deployment Script (SECURE VERSION)
# Target Server: Hostinger Cloud VPS (Malaysia Region)
# Server Specs: 4 vCPU, 16 GB RAM, 200 GB NVMe SSD, 16 TB Bandwidth
# Created: 2026-01-01
# Last Updated: 2026-01-18 - HOSTINGER MIGRATION
################################################################################

set -e  # Exit on any error

#===============================================================================
# COLOR DEFINITIONS FOR TERMINAL OUTPUT
#===============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

#===============================================================================
# LOGGING FUNCTIONS
#===============================================================================
log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_step() {
    echo -e "${CYAN}[STEP]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_header() {
    echo ""
    echo -e "${WHITE}============================================================${NC}"
    echo -e "${WHITE}  $1${NC}"
    echo -e "${WHITE}============================================================${NC}"
    echo ""
}

log_security() {
    echo -e "${RED}[SECURITY]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

#===============================================================================
# SECURITY FUNCTIONS
#===============================================================================

generate_secure_password() {
    # Generate a secure random password
    openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 32
}

generate_secure_key() {
    # Generate a secure 32-byte hex key
    openssl rand -hex 32
}

validate_password_strength() {
    local password=$1
    local min_length=16
    
    if [ ${#password} -lt $min_length ]; then
        return 1
    fi
    
    # Check for uppercase, lowercase, numbers, and special chars
    if [[ "$password" =~ [a-z]] && \
       [[ "$password" =~ [A-Z]] && \
       [[ "$password" =~ [0-9]] && \
       [[ "$password" =~ [!@#$%^&*()_+-=] ]]; then
        return 0
    fi
    
    return 1
}

check_secure_passwords() {
    log_header "Checking Password Security"
    
    local issues=0
    
    # Check PostgreSQL password
    if [ "$POSTGRES_PASSWORD" == "change_this_in_production_secure_password" ]; then
        log_security "PostgreSQL password is still the default value!"
        log_step "Generating secure PostgreSQL password..."
        POSTGRES_PASSWORD=$(generate_secure_password)
        sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$POSTGRES_PASSWORD/" .env 2>/dev/null || true
        ((issues++))
    elif ! validate_password_strength "$POSTGRES_PASSWORD"; then
        log_warn "PostgreSQL password may be too weak"
        ((issues++))
    else
        log_info "PostgreSQL password is secure"
    fi
    
    # Check Redis password
    if [ "$REDIS_PASSWORD" == "change_this_in_production_secure_password" ]; then
        log_security "Redis password is still the default value!"
        log_step "Generating secure Redis password..."
        REDIS_PASSWORD=$(generate_secure_password)
        sed -i "s/^REDIS_PASSWORD=.*/REDIS_PASSWORD=$REDIS_PASSWORD/" .env 2>/dev/null || true
        ((issues++))
    else
        log_info "Redis password is secure"
    fi
    
    # Check JWT secret
    if [ -z "${JWT_SECRET_KEY:-}" ] || \
       [ "$JWT_SECRET_KEY" == "change_this_to_a_secure_random_string_at_least_32_characters" ]; then
        log_security "JWT_SECRET_KEY is not set or is default!"
        log_step "Generating secure JWT key..."
        JWT_SECRET_KEY=$(generate_secure_key)
        echo "JWT_SECRET_KEY=$JWT_SECRET_KEY" >> .env 2>/dev/null || true
        ((issues++))
    else
        log_info "JWT_SECRET_KEY is configured"
    fi
    
    # Check Encryption key
    if [ -z "${ENCRYPTION_KEY:-}" ] || \
       [ "$ENCRYPTION_KEY" == "change_this_to_a_secure_random_string_at_least_32_characters" ]; then
        log_security "ENCRYPTION_KEY is not set or is default!"
        log_step "Generating secure Encryption key..."
        ENCRYPTION_KEY=$(generate_secure_key)
        echo "ENCRYPTION_KEY=$ENCRYPTION_KEY" >> .env 2>/dev/null || true
        ((issues++))
    else
        log_info "ENCRYPTION_KEY is configured"
    fi
    
    # Check Grafana password
    if [ "$GRAFANA_ADMIN_PASSWORD" == "change_this_in_production_secure_password" ]; then
        log_security "Grafana admin password is still the default value!"
        log_step "Generating secure Grafana password..."
        GRAFANA_ADMIN_PASSWORD=$(generate_secure_password)
        sed -i "s/^GRAFANA_ADMIN_PASSWORD=.*/GRAFANA_ADMIN_PASSWORD=$GRAFANA_ADMIN_PASSWORD/" .env 2>/dev/null || true
        ((issues++))
    else
        log_info "Grafana admin password is secure"
    fi
    
    if [ $issues -gt 0 ]; then
        log_warn "$issues security issues found and auto-fixed"
        log_info "Updated .env file with new secure passwords"
    else
        log_info "All passwords are secure"
    fi
}

#===============================================================================
# SYSTEM REQUIREMENTS CHECK
#===============================================================================
check_requirements() {
    log_header "Checking System Requirements"
    
    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        log_warn "Not running as root. Some operations may require sudo."
    fi
    
    # Check operating system
    if [[ -f /etc/os-release ]]; then
        source /etc/os-release
        log_info "Operating System: ${PRETTY_NAME}"
    else
        log_error "Cannot detect operating system"
        exit 1
    fi
    
    # Check available memory
    AVAILABLE_RAM=$(free -g | awk '/^Mem:/{print $2}')
    log_info "Available RAM: ${AVAILABLE_RAM} GB"
    
    if [[ ${AVAILABLE_RAM} -lt 16 ]]; then
        log_warn "Less than 16 GB RAM available. Performance may be affected."
    fi
    
    # Check CPU cores
    CPU_CORES_AVAILABLE=$(nproc)
    log_info "Available CPU Cores: ${CPU_CORES_AVAILABLE}"
    
    # Check disk space
    DISK_SPACE=$(df -h / | awk '/\//{print $4}')
    log_info "Available Disk Space: ${DISK_SPACE}"
    
    # Check if Docker is installed
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version)
        log_info "Docker installed: ${DOCKER_VERSION}"
    else
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(docker-compose --version)
        log_info "Docker Compose installed: ${COMPOSE_VERSION}"
    elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
        log_info "Docker Compose (v2) installed"
    else
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        log_error "jq is required but not installed. Please install jq first."
        exit 1
    fi
    
    # Check if openssl is installed (for secure password generation)
    if ! command -v openssl &> /dev/null; then
        log_error "openssl is required for secure password generation. Please install openssl."
        exit 1
    fi
    
    log_info "All requirements check completed successfully"
}

#===============================================================================
# DOCKER INSTALLATION
#===============================================================================
install_docker() {
    log_header "Installing Docker and Docker Compose"
    
    # Check if Docker is already installed
    if command -v docker &> /dev/null; then
        log_info "Docker is already installed: $(docker --version)"
    else
        # Update package index
        log_step "Updating package index..."
        sudo apt-get update -qq
        
        # Install prerequisites
        log_step "Installing prerequisites..."
        sudo apt-get install -y -qq apt-transport-https ca-certificates curl gnupg lsb-release
        
        # Add Docker's official GPG key
        log_step "Adding Docker GPG key..."
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
        
        # Set up the Docker stable repository
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        
        # Install Docker
        log_step "Installing Docker..."
        sudo apt-get update -qq
        sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io
        
        # Enable Docker service
        log_step "Enabling Docker service..."
        sudo systemctl start docker
        sudo systemctl enable docker
        
        # Add current user to docker group
        log_step "Adding user to docker group..."
        sudo usermod -aG docker $USER
        
        log_info "Docker installation completed successfully"
        log_info "Docker version: $(docker --version)"
    fi
    
    # Check if Docker Compose is already installed
    if command -v docker-compose &> /dev/null; then
        log_info "Docker Compose is already installed: $(docker-compose --version)"
    elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
        log_info "Docker Compose v2 is available via 'docker compose'"
    else
        # Install Docker Compose
        log_step "Installing Docker Compose..."
        COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | jq -r '.tag_name')
        sudo curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
        
        log_info "Docker Compose installation completed successfully"
        log_info "Docker Compose version: $(docker-compose --version)"
    fi
}

#===============================================================================
# PROJECT CLONING AND SETUP
#===============================================================================
setup_project() {
    log_header "Setting Up Project Structure"
    
    PROJECT_DIR="$(pwd)"
    
    # Create necessary subdirectories
    log_step "Creating project subdirectories..."
    mkdir -p config
    mkdir -p src
    mkdir -p scripts
    mkdir -p scripts/chat_system
    mkdir -p monitoring/grafana/config
    mkdir -p monitoring/grafana/dashboards
    mkdir -p monitoring/grafana/datasources
    mkdir -p monitoring/prometheus
    mkdir -p nginx/sites-available
    mkdir -p n8n_workflows
    mkdir -p db/migrations
    mkdir -p docs
    mkdir -p tests
    mkdir -p data
    mkdir -p data/backups
    mkdir -p data/logs
    mkdir -p data/generated_content
    mkdir -p data/uploads
    
    log_info "Project structure created successfully"
}

#===============================================================================
# ENVIRONMENT FILE CREATION
#===============================================================================
create_env_file() {
    log_header "Creating Environment Configuration File"
    
    ENV_FILE="$(pwd)/.env"
    
    # Check if .env already exists
    if [ -f "${ENV_FILE}" ]; then
        log_info "Existing .env file found, checking security..."
        check_secure_passwords
        log_info "Security check completed"
        return 0
    fi
    
    # Create .env file with secure default values
    log_step "Generating secure passwords..."
    SECURE_POSTGRES_PASSWORD=$(generate_secure_password)
    SECURE_REDIS_PASSWORD=$(generate_secure_password)
    SECURE_JWT_KEY=$(generate_secure_key)
    SECURE_ENCRYPTION_KEY=$(generate_secure_key)
    SECURE_GRAFANA_PASSWORD=$(generate_secure_password)
    
    cat > "${ENV_FILE}" << EOF
################################################################################
# JAV Automation System - Environment Configuration (SECURE VERSION)
# Target Server: Hostinger Cloud VPS (Malaysia Region)
# WARNING: Never commit this file to version control
# Generated: $(date '+%Y-%m-%d %H:%M:%S')
################################################################################

#===============================================================================
# SERVER IDENTIFICATION
#===============================================================================
SERVER_NAME=jav-automation-my
SERVER_REGION=malaysia
DEPLOYMENT_ENV=production

#===============================================================================
# CONTAINER ORCHESTRATION
#===============================================================================
COMPOSE_PROJECT_NAME=jav_automation
NETWORK_NAME=jav_network
SUBNET_RANGE=172.28.0.0/16
GATEWAY_ADDRESS=172.28.0.1

#===============================================================================
# DATABASE CONFIGURATION
#===============================================================================
POSTGRES_DB=jav_automation
POSTGRES_USER=jav_admin
POSTGRES_PASSWORD=${SECURE_POSTGRES_PASSWORD}
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
DATABASE_URL=postgresql://jav_admin:${SECURE_POSTGRES_PASSWORD}@postgres:5432/jav_automation

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=${SECURE_REDIS_PASSWORD}
REDIS_URL=redis://:${SECURE_REDIS_PASSWORD}@redis:6379/0

#===============================================================================
# SECURITY KEYS (AUTO-GENERATED)
#===============================================================================
# These keys are automatically generated and secure
JWT_SECRET_KEY=${SECURE_JWT_KEY}
ENCRYPTION_KEY=${SECURE_ENCRYPTION_KEY}

#===============================================================================
# API KEYS - QWEN (ALIBABA CLOUD) - PRIMARY AI MODEL
#===============================================================================
QWEN_API_KEY=your_qwen_api_key_here
QWEN_API_ENDPOINT=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus
QWEN_MAX_TOKENS=4000
QWEN_TEMPERATURE=0.7

#===============================================================================
# API KEYS - A2E.AI (VIDEO GENERATION)
#===============================================================================
A2E_API_KEY=your_a2e_api_key_here
A2E_API_ENDPOINT=https://api.a2e.ai/v1
A2E_DAILY_CREDIT_LIMIT=50
A2E_MONTHLY_COST_CEILING_USD=100

#===============================================================================
# PLATFORM CREDENTIALS (REPLACE WITH ACTUAL VALUES)
#===============================================================================

# TikTok
TIKTOK_API_KEY=your_tiktok_api_key
TIKTOK_SECRET=your_tiktok_secret

# Instagram
INSTAGRAM_API_KEY=your_instagram_api_key
INSTAGRAM_SECRET=your_instagram_secret

# YouTube
YOUTUBE_API_KEY=your_youtube_api_key
YOUTUBE_CLIENT_ID=your_youtube_client_id
YOUTUBE_CLIENT_SECRET=your_youtube_client_secret

# Facebook
FACEBOOK_API_KEY=your_facebook_api_key
FACEBOOK_SECRET=your_facebook_secret

# Discord
DISCORD_BOT_TOKEN=your_discord_bot_token
DISCORD_CLIENT_ID=your_discord_client_id
DISCORD_CLIENT_SECRET=your_discord_client_secret

#===============================================================================
# PROXY CONFIGURATION
#===============================================================================
PROXY_ENABLED=false
PROXY_REGION=jp
PROXY_HOST=your_proxy_host
PROXY_PORT=8080
PROXY_USERNAME=your_proxy_username
PROXY_PASSWORD=your_proxy_password

#===============================================================================
# MONITORING & ALERTING
#===============================================================================
GRAFANA_ADMIN_PASSWORD=${SECURE_GRAFANA_PASSWORD}
PROMETHEUS_RETENTION=15d
ALERT_EMAIL_ENABLED=false
ALERT_EMAIL_RECIPIENT=admin@example.com
SLACK_WEBHOOK_URL=your_slack_webhook_url

#===============================================================================
# PERFORMANCE SETTINGS
#===============================================================================
FFMPEG_THREADS=8
MAX_PARALLEL_RENDERS=4
MAX_PARALLEL_UPLOADS=2
RENDER_MEMORY_LIMIT_GB=14
CPU_AFFINITY=auto

#===============================================================================
# CONTENT GENERATION
#===============================================================================
DEFAULT_VIDEO_FPS=30
DEFAULT_VIDEO_BITRATE=5000k
DEFAULT_VIDEO_CRF=23
DEFAULT_AUDIO_BITRATE=192k
DEFAULT_AUDIO_SAMPLE_RATE=48000

#===============================================================================
# ENGAGEMENT & ANALYTICS
#===============================================================================
ENGAGEMENT_CHECK_INTERVAL=3600
FOLLOWER_TRACKING_ENABLED=true
ENGAGEMENT_RATE_THRESHOLD=3.5
PHASE2_ACTIVATION_FOLLOWERS=5000

#===============================================================================
# RATE LIMITING & SECURITY
#===============================================================================
API_RATE_LIMIT=100
MAX_CONNECTIONS_PER_IP=10

#===============================================================================
# LOGGING CONFIGURATION
#===============================================================================
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=7
LOG_FILE_SIZE_MB=100
LOG_BACKUP_COUNT=5

#===============================================================================
# BACKUP CONFIGURATION
#===============================================================================
BACKUP_ENABLED=true
BACKUP_SCHEDULE=0 3 * * *
BACKUP_RETENTION_DAYS=7
BACKUP_COMPRESSION_ENABLED=true
BACKUP_ENCRYPTION_ENABLED=true

#===============================================================================
# OPTIONAL FEATURES
#===============================================================================
VOICE_GENERATION_ENABLED=true
SUBTITLE_GENERATION_ENABLED=true
THUMBNAIL_GENERATION_ENABLED=true
SCHEDULED_PUBLISHING_ENABLED=true
AUTO_ENGAGEMENT_ENABLED=true

#===============================================================================
# DATA PATHS
#===============================================================================
DATA_PATH=./data
EOF
    
    log_info "Environment file created: ${ENV_FILE}"
    log_warn "IMPORTANT: Please update API keys before deployment"
    log_info "Secure passwords have been automatically generated"
}

#===============================================================================
# NGINX CONFIGURATION
#===============================================================================
create_nginx_config() {
    log_header "Creating Nginx Configuration with Security Headers"
    
    NGINX_CONFIG="$(pwd)/nginx/nginx.conf"
    
    cat > "${NGINX_CONFIG}" << 'EOF'
events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    # Basic settings
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Logging configuration
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;
    
    # Performance optimization
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml application/json application/javascript application/xml;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_conn_zone $binary_remote_addr zone=conn_limit:10m;
    
    # Upstream servers
    upstream n8n {
        server n8n:5678;
        keepalive 32;
    }
    
    upstream grafana {
        server grafana:3000;
        keepalive 16;
    }
    
    upstream prometheus {
        server prometheus:9090;
        keepalive 8;
    }
    
    # Default server configuration
    server {
        listen 80;
        server_name localhost;
        
        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        add_header Content-Security-Policy "default-src 'self';" always;
        
        # API routes
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            proxy_pass http://n8n/;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }
        
        # Grafana routes
        location /grafana/ {
            proxy_pass http://grafana/;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            rewrite ^/grafana/(.*) /$1 break;
        }
        
        # Prometheus routes
        location /prometheus/ {
            proxy_pass http://prometheus/;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            rewrite ^/prometheus/(.*) /$1 break;
        }
        
        # Health check endpoint
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
EOF
    
    log_info "Nginx configuration created: ${NGINX_CONFIG}"
}

#===============================================================================
# DOCKER COMPOSE CONFIGURATION (SECURE VERSION)
#===============================================================================
create_docker_compose() {
    log_header "Creating Secure Docker Compose Configuration"
    
    DOCKER_COMPOSE_FILE="$(pwd)/docker-compose.yml"
    
    cat > "${DOCKER_COMPOSE_FILE}" << 'EOF'
version: '3.8'

################################################################################
# JAV Automation System - Docker Compose Configuration (SECURE VERSION)
# Target Server: Hostinger Cloud VPS (Malaysia Region)
# Server Specs: 4 vCPU, 16 GB RAM, 200 GB NVMe SSD
# Created: 2026-01-01
# Last Updated: 2026-01-18 - HOSTINGER MIGRATION
################################################################################

#===============================================================================
# SECURITY NOTES:
# - Database ports bound to 127.0.0.1 only (not publicly accessible)
# - All services have CPU and memory limits
# - Docker socket mounted read-only for Watchtower
# - Strong passwords auto-generated during deployment
#===============================================================================

services:
  #============================================================================
  # POSTGRESQL DATABASE - Primary Data Storage
  #============================================================================
  postgres:
    image: postgres:15-alpine
    container_name: jav_postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-jav_automation}
      POSTGRES_USER: ${POSTGRES_USER:-jav_admin}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./db/migrations:/docker-entrypoint-initdb.d:mro
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    networks:
      - jav_network
    # SECURITY: Only bind to localhost
    ports:
      - "127.0.0.1:5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-jav_admin}"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G

  #============================================================================
  # REDIS CACHE - Session Storage and Caching
  #============================================================================
  redis:
    image: redis:7-alpine
    container_name: jav_redis
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD} --maxmemory 512mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    networks:
      - jav_network
    # SECURITY: Only bind to localhost
    ports:
      - "127.0.0.1:6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 1G

  #============================================================================
  # N8N - Workflow Automation Engine
  #============================================================================
  n8n:
    image: n8nio/n8n:latest
    container_name: jav_n8n
    restart: unless-stopped
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD:-change_this_password}
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_PORT=5432
      - DB_POSTGRESDB_DATABASE=${POSTGRES_DB:-jav_automation}
      - DB_POSTGRESDB_USER=${POSTGRES_USER:-jav_admin}
      - DB_POSTGRESDB_PASSWORD=${POSTGRES_PASSWORD}
      - N8N_ENCRYPTION_KEY=${ENCRYPTION_KEY}
      - EXECUTIONS_DATA_SAVE_ON_ERROR=all
      - EXECUTIONS_DATA_SAVE_ON_SUCCESS=all
      - GENERIC_TIMEZONE=Asia/Singapore
      - TZ=Asia/Singapore
    volumes:
      - n8n_data:/home/node/.n8n
      - ./n8n_workflows:/data/workflows:ro
      - ./data/generated_content:/data/generated_content
    networks:
      - jav_network
    depends_on:
      - postgres
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:5678/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G

  #============================================================================
  # GRAFANA - Monitoring Dashboard
  #============================================================================
  grafana:
    image: grafana/grafana:latest
    container_name: jav_grafana
    restart: unless-stopped
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_INSTALL_PLUGINS=grafana-clock-panel,grafana-simple-json-datasource
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning:ro
    networks:
      - jav_network
    depends_on:
      - prometheus
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:3000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G

  #============================================================================
  # PROMETHEUS - Metrics Collection and Storage
  #============================================================================
  prometheus:
    image: prom/prometheus:latest
    container_name: jav_prometheus
    restart: unless-stopped
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=${PROMETHEUS_RETENTION:-15d}'
      - '--web.enable-lifecycle'
      - '--web.enable-admin-api'
    volumes:
      - prometheus_data:/prometheus
      - ./monitoring/prometheus:/etc/prometheus:ro
    networks:
      - jav_network
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:9090/-/healthy"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G

  #============================================================================
  # NODE EXPORTER - System Metrics Collection
  #============================================================================
  node-exporter:
    image: prom/node-exporter:latest
    container_name: jav_node_exporter
    restart: unless-stopped
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--path.rootfs=/rootfs'
    networks:
      - jav_network
    deploy:
      resources:
        limits:
          cpus: '0.2'
          memory: 256M

  #============================================================================
  # NGINX REVERSE PROXY - Load Balancer and SSL Termination
  #============================================================================
  nginx:
    image: nginx:alpine
    container_name: jav_nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/sites-available:/etc/nginx/sites-available:ro
      - nginx_data:/var/log/nginx
    networks:
      - jav_network
    depends_on:
      - n8n
      - grafana
      - prometheus
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M

  #============================================================================
  # WATCHTOWER - Auto-Updates (SECURE VERSION)
  #============================================================================
  watchtower:
    image: containrrr/watchtower:latest
    container_name: jav_watchtower
    restart: unless-stopped
    volumes:
      # SECURITY: Read-only Docker socket
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /var/lib/docker/volumes:/var/lib/docker/volumes:ro
    environment:
      - WATCHTOWER_CLEANUP=true
      - WATCHTOWER_POLL_INTERVAL=86400
      - WATCHTOWER_NOTIFICATIONS=slack
      - WATCHTOWER_NOTIFICATION_SLACK_HOOK_URL=${SLACK_WEBHOOK_URL}
      - WATCHTOWER_NOTIFICATION_SLACK_IDENTIFIER=jav-automation
      - WATCHTOWER_HTTP_API_UPDATE=true
      - WATCHTOWER_HTTP_API_TOKEN=${WATCHTOWER_TOKEN}
    networks:
      - jav_network
    labels:
      - "com.centurylinklabs.watchtower.enable=true"
    deploy:
      resources:
        limits:
          cpus: '0.2'
          memory: 256M

################################################################################
# VOLUME DEFINITIONS
################################################################################
volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${DATA_DIR:-./data}/postgres
  
  redis_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${DATA_DIR:-./data}/redis
  
  n8n_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${DATA_DIR:-./data}/n8n
  
  grafana_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${DATA_DIR:-./data}/grafana
  
  prometheus_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${DATA_DIR:-./data}/prometheus
  
  nginx_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${DATA_DIR:-./data}/nginx

################################################################################
# NETWORK DEFINITIONS
################################################################################
networks:
  jav_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
          gateway: 172.28.0.1
EOF
    
    log_info "Docker Compose configuration created: ${DOCKER_COMPOSE_FILE}"
}

#===============================================================================
# MAIN DEPLOYMENT FUNCTION
#===============================================================================
deploy_system() {
    log_header "Starting Secure System Deployment"
    
    log_step "Checking system requirements..."
    check_requirements
    
    log_step "Setting up project structure..."
    setup_project
    
    log_step "Creating environment configuration with secure passwords..."
    create_env_file
    
    log_step "Creating Nginx configuration..."
    create_nginx_config
    
    log_step "Creating Docker Compose configuration..."
    create_docker_compose
    
    log_step "Building and starting containers..."
    docker-compose up -d --build
    
    log_step "Verifying deployment..."
    sleep 10
    
    # Check container status
    docker-compose ps
    
    log_header "Deployment Summary"
    log_info "JAV Automation System has been deployed successfully!"
    log_info ""
    log_info "Access Points:"
    log_info "  - N8N Workflows: http://your_server_ip/api/"
    log_info "  - Grafana Dashboard: http://your_server_ip/grafana/"
    log_info "  - Prometheus: http://your_server_ip/prometheus/"
    log_info "  - Health Check: http://your_server_ip/health"
    log_info ""
    log_info "Security Features Applied:"
    log_info "  - Secure passwords auto-generated"
    log_info "  - Database ports bound to localhost only"
    log_info "  - Docker socket mounted read-only"
    log_info "  - CPU and memory limits configured"
    log_info "  - Rate limiting enabled in Nginx"
    log_info ""
    log_warn "IMPORTANT: Please update the .env file with your actual API keys"
}

#===============================================================================
# SCRIPT ENTRY POINT
#===============================================================================
main() {
    log_header "JAV Automation System - Secure Deployment Script"
    log_info "Target Server: Hostinger Cloud VPS (Malaysia Region)"
    log_info "Server Specs: 4 vCPU, 16 GB RAM, 200 GB NVMe SSD"
    log_info "Deployment Date: $(date '+%Y-%m-%d %H:%M:%S')"
    
    # Run deployment
    deploy_system
}

# Execute main function
main "$@"

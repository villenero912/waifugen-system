#!/bin/bash
# Quick Setup Script for Content Automation System
# Optimized for VPS deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_NAME="content-automation"
PROJECT_DIR="/opt/$PROJECT_NAME"
LOG_FILE="/var/log/$PROJECT_NAME-setup.log"

# Functions
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" | tee -a "$LOG_FILE"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}" | tee -a "$LOG_FILE"
}

check_requirements() {
    info "Checking system requirements..."
    
    # Check if running as root
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root. Run as regular user with sudo."
    fi
    
    # Check Ubuntu version
    if ! grep -q "Ubuntu" /etc/os-release; then
        warning "This script is optimized for Ubuntu 20.04+"
    fi
    
    # Check available memory
    MEMORY_GB=$(free -g | awk '/^Mem:/{print $2}')
    if [[ $MEMORY_GB -lt 4 ]]; then
        error "Minimum 4GB RAM required. Detected: ${MEMORY_GB}GB"
    fi
    
    # Check available disk space
    DISK_GB=$(df -BG / | awk 'NR==2{print $4}' | sed 's/G//')
    if [[ $DISK_GB -lt 50 ]]; then
        error "Minimum 50GB disk space required. Available: ${DISK_GB}GB"
    fi
    
    log "System requirements check passed"
}

install_dependencies() {
    info "Installing system dependencies..."
    
    # Update package list
    sudo apt update -y
    
    # Install essential packages
    sudo apt install -y \
        curl \
        wget \
        git \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        ffmpeg \
        sqlite3 \
        redis-server \
        postgresql-client \
        docker.io \
        docker-compose \
        nginx \
        certbot \
        python3-certbot-nginx \
        htop \
        iotop \
        fail2ban \
        ufw \
        bc \
        jq
    
    # Install Node.js for N8N (optional)
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
    
    log "Dependencies installed successfully"
}

setup_project() {
    info "Setting up project structure..."
    
    # Create project directory
    sudo mkdir -p "$PROJECT_DIR"
    sudo chown $USER:$USER "$PROJECT_DIR"
    
    # Create virtual environment
    cd "$PROJECT_DIR"
    python3 -m venv venv
    source venv/bin/activate
    
    # Install Python dependencies
    pip install --upgrade pip
    pip install \
        aiohttp \
        asyncio \
        requests \
        pyyaml \
        cryptography \
        sqlite3 \
        psutil \
        prometheus-client \
        schedule \
        python-dotenv \
        jinja2 \
        flask \
        flask-socketio \
        celery \
        redis \
        sqlalchemy \
        alembic
    
    log "Project structure created"
}

configure_system() {
    info "Configuring system optimizations..."
    
    # Configure swap
    sudo fallocate -l 2G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    
    # Configure kernel parameters
    sudo tee /etc/sysctl.d/99-automation-optimization.conf > /dev/null <<EOF
# Network optimizations
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.ipv4.tcp_rmem = 4096 65536 134217728
net.ipv4.tcp_congestion_control = bbr
net.ipv4.tcp_fastopen = 3

# Memory optimizations
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5

# File system optimizations
fs.file-max = 2097152
EOF
    
    sudo sysctl -p /etc/sysctl.d/99-automation-optimization.conf
    
    log "System optimizations applied"
}

setup_firewall() {
    info "Configuring firewall and security..."
    
    # Configure UFW
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow ssh
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw allow 8080/tcp  # Main dashboard
    sudo ufw allow 3000/tcp  # Grafana
    sudo ufw allow 9090/tcp  # Prometheus
    sudo ufw --force enable
    
    # Configure fail2ban
    sudo systemctl enable fail2ban
    sudo systemctl start fail2ban
    
    log "Firewall and security configured"
}

create_docker_config() {
    info "Creating Docker configuration..."
    
    cd "$PROJECT_DIR"
    
    # Create docker-compose.yml
    cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  automation-main:
    build: .
    container_name: automation_main
    restart: unless-stopped
    ports:
      - "8080:8080"
    environment:
      - PYTHONPATH=/app/src
    volumes:
      - ./:/app
      - ./logs:/app/logs
      - ./data:/app/data
      - ./.env:/app/.env
    networks:
      - automation_net
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:14
    container_name: automation_postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: automation_db
      POSTGRES_USER: automation_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - automation_net
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    container_name: automation_redis
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - automation_net
    ports:
      - "6379:6379"

  grafana:
    image: grafana/grafana
    container_name: automation_grafana
    restart: unless-stopped
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - automation_net
    ports:
      - "3000:3000"

  prometheus:
    image: prom/prometheus
    container_name: automation_prometheus
    restart: unless-stopped
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    networks:
      - automation_net
    ports:
      - "9090:9090"

volumes:
  postgres_data:
  redis_data:
  grafana_data:
  prometheus_data:

networks:
  automation_net:
    driver: bridge
EOF
    
    log "Docker configuration created"
}

create_startup_scripts() {
    info "Creating startup scripts..."
    
    cd "$PROJECT_DIR"
    
    # Start script
    cat > start.sh << 'EOF'
#!/bin/bash
cd /opt/content-automation
source venv/bin/activate
docker-compose up -d
echo "Automation system started"
echo "Dashboard: http://localhost:8080"
echo "Grafana: http://localhost:3000"
echo "Prometheus: http://localhost:9090"
EOF
    
    # Stop script
    cat > stop.sh << 'EOF'
#!/bin/bash
cd /opt/content-automation
docker-compose down
echo "Automation system stopped"
EOF
    
    # Status script
    cat > status.sh << 'EOF'
#!/bin/bash
cd /opt/content-automation
echo "=== AUTOMATION SYSTEM STATUS ==="
docker-compose ps
echo ""
echo "=== SYSTEM RESOURCES ==="
echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')%"
echo "Memory: $(free | grep Mem | awk '{printf("%.1f%%"), $3/$2 * 100.0}')"
echo "Disk: $(df -h / | awk 'NR==2{print $5}')"
echo ""
echo "=== RECENT LOGS ==="
tail -n 10 automation.log
EOF
    
    chmod +x start.sh stop.sh status.sh
    
    log "Startup scripts created"
}

create_monitoring_config() {
    info "Creating monitoring configuration..."
    
    cd "$PROJECT_DIR"
    mkdir -p monitoring
    
    # Prometheus configuration
    cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
  
  - job_name: 'automation-system'
    static_configs:
      - targets: ['automation-main:8080']
  
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']
EOF
    
    # Alert rules
    cat > monitoring/alert_rules.yml << 'EOF'
groups:
  - name: automation_alerts
    rules:
      - alert: HighCPUUsage
        expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: High CPU usage detected
          description: "CPU usage is above 80%"
      
      - alert: HighMemoryUsage
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: High memory usage detected
          description: "Memory usage is above 85%"
EOF
    
    log "Monitoring configuration created"
}

setup_dns() {
    info "Configuring DNS optimization..."
    
    # Backup original resolv.conf
    sudo cp /etc/resolv.conf /etc/resolv.conf.backup
    
    # Configure optimized DNS
    sudo tee /etc/resolv.conf > /dev/null <<EOF
nameserver 1.1.1.1
nameserver 8.8.8.8
options timeout:2 attempts:3 rotate
EOF
    
    log "DNS optimization configured"
}

final_setup() {
    info "Performing final setup..."
    
    cd "$PROJECT_DIR"
    
    # Copy source files
    cp -r ../src ./
    cp -r ../config ./
    
    # Create environment file
    cp ../.env.example .env
    chmod 600 .env
    
    # Create log directory
    mkdir -p logs data
    
    # Set permissions
    chown -R $USER:$USER "$PROJECT_DIR"
    
    log "Final setup completed"
}

display_completion_info() {
    echo ""
    echo -e "${GREEN}SETUP COMPLETED SUCCESSFULLY!${NC}"
    echo "========================================"
    echo ""
    echo -e "${BLUE}NEXT STEPS:${NC}"
    echo "1. Configure API keys in: $PROJECT_DIR/.env"
    echo "2. Start the system: cd $PROJECT_DIR && ./start.sh"
    echo "3. Access dashboard: http://localhost:8080"
    echo ""
    echo -e "${BLUE}SYSTEM COMMANDS:${NC}"
    echo "   Start:  ./start.sh"
    echo "   Stop:   ./stop.sh"
    echo "   Status: ./status.sh"
    echo ""
    echo -e "${GREEN}Your automation system is ready to deploy!${NC}"
}

main() {
    echo -e "${BLUE}"
    echo "CONTENT AUTOMATION SYSTEM SETUP"
    echo "========================================"
    echo "Optimized for VPS deployment"
    echo -e "${NC}"
    
    check_requirements
    install_dependencies
    setup_project
    configure_system
    setup_firewall
    create_docker_config
    create_startup_scripts
    create_monitoring_config
    setup_dns
    final_setup
    display_completion_info
    
    log "Setup completed successfully"
}

# Run main function
main "$@"

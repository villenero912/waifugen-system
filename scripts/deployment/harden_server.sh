#!/bin/bash

################################################################################
# WaifuGen - Server Hardening Script
# Purpose: Configure Firewall (UFW) and SSH Security
################################################################################

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   log_error "This script must be run as root (use sudo)"
   exit 1
fi

log_info "Starting Server Hardening..."

# 1. Update system
log_info "Updating system packages..."
apt-get update -qq && apt-get upgrade -y -qq

# 2. Install essential security tools
log_info "Installing security tools (ufw, fail2ban)..."
apt-get install -y -qq ufw fail2ban

# 3. Configure UFW (Firewall)
log_info "Configuring UFW (Uncomplicated Firewall)..."
ufw default deny incoming
ufw default allow outgoing

# Allow standard ports
ufw allow ssh          # Port 22
ufw allow http         # Port 80
ufw allow https        # Port 443

# Enable UFW
log_warn "Enabling UFW. Make sure you don't lose access to port 22!"
echo "y" | ufw enable

# 4. Hardening SSH
log_info "Hardening SSH configuration..."
SSH_CONFIG="/etc/ssh/sshd_config"

# Backup existing config
cp $SSH_CONFIG "${SSH_CONFIG}.bak_$(date +%F_%T)"

# Security tweaks
# - Disable root login
sed -i 's/^#PermitRootLogin.*/PermitRootLogin no/' $SSH_CONFIG
sed -i 's/^PermitRootLogin.*/PermitRootLogin no/' $SSH_CONFIG

# - Limit max auth attempts
sed -i 's/^#MaxAuthTries.*/MaxAuthTries 3/' $SSH_CONFIG
sed -i 's/^MaxAuthTries.*/MaxAuthTries 3/' $SSH_CONFIG

# - Disable empty passwords
sed -i 's/^#PermitEmptyPasswords.*/PermitEmptyPasswords no/' $SSH_CONFIG
sed -i 's/^PermitEmptyPasswords.*/PermitEmptyPasswords no/' $SSH_CONFIG

# Restart SSH
log_info "Restarting SSH service..."
systemctl restart ssh

# 5. Fail2Ban configuration
log_info "Configuring Fail2Ban for SSH protection..."
cat > /etc/fail2ban/jail.local << EOF
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
EOF

systemctl restart fail2ban

log_info "------------------------------------------------------------"
log_info "SERVER HARDENING COMPLETED SUCCESSFULLY"
log_info "------------------------------------------------------------"
log_warn "Summary of changes:"
log_warn " - UFW enabled: Only ports 22, 80, 443 are open."
log_warn " - SSH Hardened: Root login disabled, max attempts limited."
log_warn " - Fail2Ban active: Brute force protection enabled."
log_info "------------------------------------------------------------"

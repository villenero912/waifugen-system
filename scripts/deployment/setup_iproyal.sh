#!/bin/bash
# ============================================
# ELITE 8 - IPRoyal Proxy Setup Script
# ============================================
# This script helps configure IPRoyal proxies
# for the Elite 8 AI Video Generation System
#
# Budget: €15/month (~10GB residential proxies)
# Provider: https://iproyal.com
# Discount Code: IPR50
# ============================================

set -e  # Exit on error

echo "============================================"
echo "ELITE 8 - IPRoyal Proxy Configuration"
echo "============================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check if .env exists
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Creating from template..."
    cp config/.env.example .env
    print_status "Created .env file. Please edit it with your credentials."
    echo ""
    echo "Next steps:"
    echo "1. Edit .env and fill in your IPRoyal credentials"
    echo "2. Run this script again to verify configuration"
    exit 0
fi

# Source the .env file
set -a  # Auto-export variables
source .env
set +a

echo "Step 1: Verifying IPRoyal Configuration"
echo "----------------------------------------"

# Check if IPRoyal is enabled
if [ "$IPROYAL_ENABLED" != "true" ]; then
    print_warning "IPROYAL_ENABLED is not set to 'true'"
    print_status "To enable, edit .env and set: IPOYAL_ENABLED=true"
else
    print_status "IPRoyal is enabled"
fi

# Check credentials
if [ -z "$IPROYAL_USERNAME" ] || [ "$IPROYAL_USERNAME" = "your_iproyal_username" ]; then
    print_error "IPROYAL_USERNAME not configured"
    echo "  Edit .env and set your IPRoyal username"
else
    print_status "IPROYAL_USERNAME configured"
fi

if [ -z "$IPROYAL_PASSWORD" ] || [ "$IPROYAL_PASSWORD" = "your_iproyal_password" ]; then
    print_error "IPROYAL_PASSWORD not configured"
    echo "  Edit .env and set your IPRoyal password"
else
    print_status "IPROYAL_PASSWORD configured"
fi

if [ -z "$IPROYAL_HOST" ] || [ "$IPROYAL_HOST" = "geo.iproyal.com" ]; then
    print_warning "Using default IPRoyal host: geo.iproyal.com"
else
    print_status "IPROYAL_HOST: $IPROYAL_HOST"
fi

echo ""
echo "Step 2: Budget Configuration"
echo "----------------------------------------"

# Calculate estimated costs
MONTHLY_GB=${IPROYAL_MONTHLY_GB_LIMIT:-10}
DAILY_GB=${IPROYAL_DAILY_GB_LIMIT:-0.5}

echo "Monthly GB limit: $MONTHLY_GB GB"
echo "Daily GB limit: $DAILY_GB GB"
echo ""

# Cost calculation
REGULAR_PRICE_PER_GB=7.00
DISCOUNTED_PRICE_PER_GB=1.75

REGULAR_COST=$(echo "$MONTHLY_GB * $REGULAR_PRICE_PER_GB" | bc)
DISCOUNTED_COST=$(echo "$MONTHLY_GB * $DISCOUNTED_PRICE_PER_GB" | bc)

echo "Cost estimates (at $MONTHLY_GB GB/month):"
echo "  Regular price: \$$REGULAR_COST USD/month"
echo "  With IPR50 code: \$$DISCOUNTED_COST USD/month (~€15)"
echo "  Savings: \$(echo "$REGULAR_COST - $DISCOUNTED_COST" | bc) USD/month"
echo ""

# Verify config file exists
if [ -f "config/social/iproyal_config.json" ]; then
    print_status "IPRoyal config file found: config/social/iproyal_config.json"
else
    print_error "IPRoyal config file not found"
    echo "  Expected: config/social/iproyal_config.json"
fi

echo ""
echo "Step 3: Testing Proxy Connection"
echo "----------------------------------------"

# Test if proxy is configured and enabled
if [ "$IPROYAL_ENABLED" = "true" ] && [ -n "$IPROYAL_USERNAME" ] && [ -n "$IPROYAL_PASSWORD" ]; then
    echo "Testing proxy connection..."
    
    PROXY_URL="http://$IPROYAL_USERNAME:$IPROYAL_PASSWORD@$IPROYAL_HOST:$IPROYAL_PORT"
    
    # Try to make a simple request through the proxy
    if command -v curl &> /dev/null; then
        if curl -s --proxy "$PROXY_URL" --max-time 10 https://api.ipify.org?format=json &> /dev/null; then
            print_status "Proxy connection successful!"
            echo "  Your IP is being routed through IPRoyal"
        else
            print_warning "Could not connect through proxy"
            echo "  This could be normal if the proxy is busy"
            echo "  Try running: curl -v --proxy '$PROXY_URL' https://api.ipify.org"
        fi
    else
        print_warning "curl not available for testing"
        echo "  Skipping connection test"
    fi
else
    print_warning "Proxy not fully configured. Skipping connection test."
fi

echo ""
echo "Step 4: Python Dependencies"
echo "----------------------------------------"

# Check if Python is available
if command -v python3 &> /dev/null; then
    print_status "Python3 available"
    
    # Check if required packages are installed
    echo "Checking required packages..."
    
    if python3 -c "import aiohttp" 2>/dev/null; then
        print_status "aiohttp installed"
    else
        print_warning "aiohttp not installed"
        echo "  Install with: pip install aiohttp"
    fi
    
    if python3 -c "import asyncio" 2>/dev/null; then
        print_status "asyncio available"
    else
        print_warning "asyncio not available"
    fi
else
    print_warning "Python3 not available"
fi

echo ""
echo "============================================"
echo "Setup Summary"
echo "============================================"
echo ""
echo "To complete IPRoyal configuration:"
echo ""
echo "1. Sign up at: https://iproyal.com"
echo "   - Use discount code: IPR50"
echo "   - Deposit ~\$17.50 (for 10GB with discount)"
echo ""
echo "2. Edit .env file and set:"
echo "   - IPOYAL_ENABLED=true"
echo "   - IPOYAL_USERNAME=your_username"
echo "   - IPOYAL_PASSWORD=your_password"
echo ""
echo "3. Run this script again to verify"
echo ""
echo "4. Test with Python:"
echo "   python3 -c 'from src.social import check_proxy_status; print(check_proxy_status())'"
echo ""
echo "Budget: €15/month for ~10GB residential proxies"
echo "Provider: IPRoyal (https://iproyal.com)"
echo "Discount: IPR50 for \$1.75/GB (regular \$7/GB)"
echo ""
print_status "IPRoyal proxy setup complete!"

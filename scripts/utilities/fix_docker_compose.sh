#!/bin/bash
# Fix docker-compose.yml CPU limits format issue
# This script fixes the "expected type 'string', got unconvertible type 'float64'" error

cd /root/waifugen-system/waifugen_system

echo "🔧 Fixing docker-compose.yml CPU limits..."

# Backup original
cp docker-compose.yml docker-compose.yml.backup

# Fix CPU limits - wrap numbers in quotes
sed -i 's/cpus: \([0-9.]*\)/cpus: "\1"/g' docker-compose.yml

echo "✅ Fixed! Differences:"
diff docker-compose.yml.backup docker-compose.yml || echo "No CPU limits found to fix"

echo ""
echo "🚀 Now run:"
echo "docker-compose down"
echo "docker-compose up -d"

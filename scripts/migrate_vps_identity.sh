#!/bin/bash
set -e

# Configuration
OLD_DIR="/opt/dhamma-channel-automation"
NEW_DIR="/opt/flowbiz-client-dhamma"
OLD_REPO_URL="https://github.com/natbkgift/dhamma-channel-automation.git"
NEW_REPO_URL="https://github.com/01bkgift/flowbiz-client-dhamma.git"
OLD_SERVICE_NAME="dhamma-automation"
NEW_SERVICE_NAME="flowbiz-client-dhamma"
BACKUP_DIR="/opt/migration_backup_$(date +%Y%m%d_%H%M%S)"

echo "🚀 Starting VPS Identity Migration..."
echo "Old Directory: $OLD_DIR"
echo "New Directory: $NEW_DIR"

# 1. Check if we are already migrated
if [ -d "$NEW_DIR" ] && [ ! -d "$OLD_DIR" ]; then
    echo "✅ New directory exists and old directory is gone. Migration might have already happened."
    echo "Verifying git remote..."
    cd "$NEW_DIR"
    CURRENT_REMOTE=$(git remote get-url origin)
    if [[ "$CURRENT_REMOTE" == *"$NEW_SERVICE_NAME"* ]]; then
        echo "✅ Git remote matches new identity. Stopping migration."
        exit 0
    else
        echo "⚠️ Directory matches but git remote is old. Proceeding with git update only."
        git remote set-url origin "$NEW_REPO_URL"
        echo "✅ Git remote updated."
        exit 0
    fi
fi

# 2. Check existence of old directory
if [ ! -d "$OLD_DIR" ]; then
    echo "❌ Old directory $OLD_DIR not found. Cannot proceed."
    exit 1
fi

# 3. Validation & Confirmation
echo "⚠️  This will stop services and rename directories on PRODUCTION."
read -p "Are you sure you want to continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# 4. Backup
echo "📦 Backing up critical files..."
mkdir -p "$BACKUP_DIR"
cp "$OLD_DIR/.env" "$BACKUP_DIR/" 2>/dev/null || echo "⚠️ .env not found"
if [ -f "/etc/nginx/sites-available/$OLD_SERVICE_NAME.conf" ]; then
    cp "/etc/nginx/sites-available/$OLD_SERVICE_NAME.conf" "$BACKUP_DIR/"
fi
echo "✅ Backup created at $BACKUP_DIR"

# 5. Stop Services
echo "🛑 Stopping services..."
cd "$OLD_DIR"
docker compose down || echo "⚠️ Docker down failed, continuing..."

# 6. Rename Directory
echo "🚚 Renaming directory..."
cd /opt
mv "$OLD_DIR" "$NEW_DIR"
cd "$NEW_DIR"
echo "✅ Directory renamed."

# 7. Update Git Remote & Fetch
echo "🔄 Updating Git..."
git remote set-url origin "$NEW_REPO_URL"
# Fetch latest changes to ensure we have the renamed files locally
git fetch origin
git reset --hard origin/main
echo "✅ Codebase updated to latest main."

# 8. Update Environment Variables (.env)
echo "📝 Updating .env..."
if [ -f .env ]; then
    sed -i "s|APP_SERVICE_NAME=$OLD_SERVICE_NAME|APP_SERVICE_NAME=$NEW_SERVICE_NAME|g" .env
    sed -i "s|APP_NAME=$OLD_SERVICE_NAME|APP_NAME=$NEW_SERVICE_NAME|g" .env
    # Optional: Update session cookie name only if it exists
    sed -i "s|SESSION_COOKIE_NAME=dhamma_session|SESSION_COOKIE_NAME=flowbiz_session|g" .env || true
    echo "✅ .env updated."
else
    echo "⚠️ .env not found, skipping update."
fi

# 9. Update Nginx Configuration
echo "🔧 Updating Nginx..."
OLD_NGINX_CONF="/etc/nginx/sites-available/$OLD_SERVICE_NAME.conf"
NEW_NGINX_CONF="/etc/nginx/sites-available/$NEW_SERVICE_NAME.conf"

if [ -f "$OLD_NGINX_CONF" ]; then
    # Move and rename config file
    mv "$OLD_NGINX_CONF" "$NEW_NGINX_CONF"
    
    # Update contents
    sed -i "s|$OLD_SERVICE_NAME|$NEW_SERVICE_NAME|g" "$NEW_NGINX_CONF"
    sed -i "s|upstream dhamma_backend|upstream flowbiz_dhamma_backend|g" "$NEW_NGINX_CONF"
    sed -i "s|http://dhamma_backend|http://flowbiz_dhamma_backend|g" "$NEW_NGINX_CONF"
    # Update log paths
    sed -i "s|/var/log/nginx/dhamma-|/var/log/nginx/flowbiz-dhamma-|g" "$NEW_NGINX_CONF"

    # Symlink management
    rm -f "/etc/nginx/sites-enabled/$OLD_SERVICE_NAME.conf"
    ln -sf "$NEW_NGINX_CONF" "/etc/nginx/sites-enabled/$NEW_SERVICE_NAME.conf"
    
    # Reload Nginx
    nginx -t && systemctl reload nginx
    echo "✅ Nginx updated and reloaded."
else
    echo "⚠️ Nginx config not found at $OLD_NGINX_CONF, skipping Nginx update."
fi

# 10. Start Services
echo "🚀 Starting services..."
cd "$NEW_DIR"
# Use flowbiz_port.env if available, else default behavior
if [ -f "config/flowbiz_port.env" ]; then
    docker compose --env-file config/flowbiz_port.env up -d
else
    docker compose up -d
fi

# 11. Verification
echo "🔍 Verifying services..."
sleep 5
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3007/healthz || echo "failed")

if [ "$HEALTH_CHECK" == "200" ]; then
    echo "✅ Migration SUCCESS! Service is healthy."
else
    echo "⚠️ Service check returned $HEALTH_CHECK. Please verify manually."
fi

echo "🎉 VPS Migration Complete."

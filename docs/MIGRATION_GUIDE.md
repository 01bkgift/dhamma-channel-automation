# 🚚 VPS Identity Migration Guide

This guide details the procedure for migrating the production VPS from the old identity (`dhamma-channel-automation`) to the new FlowBiz Client identity (`flowbiz-client-dhamma`).

## ⚠️ Important Warning

This migration involves **stopping production services** and changing directory names. While a rollback mechanism is implicit (backup folder created), please perform this during a maintenance window.

---

## 📋 Prerequisites

1. **SSH Access**: You must have SSH access to the `flowbiz-vps`.
2. **Sudo Privileges**: The script requires `sudo` (or root) to move directories and reload Nginx.
3. **Git Access**: The VPS must have access to pull from the new repository `01bkgift/flowbiz-client-dhamma`.

---

## 🚀 Migration Steps

### 1. Connect to VPS

SSH into your production server:

```bash
ssh user@flowbiz-vps
```

### 2. Copy the Migration Script

Since the repository on the VPS is likely still the old one, you can clone the new repo in a temp folder OR just copy-paste the script content.

**Option A: One-line (Recommended for existing setups)**

Since you are already synced locally, you can SCP the script to the server:

```bash
# Run this from your LOCAL machine
scp scripts/migrate_vps_identity.sh user@flowbiz-vps:/tmp/migrate_vps_identity.sh
```

**Option B: Create manually on VPS**

```bash
# On VPS
nano /tmp/migrate_vps_identity.sh
# Paste the content of scripts/migrate_vps_identity.sh
chmod +x /tmp/migrate_vps_identity.sh
```

### 3. Execute Migration

Run the script with root privileges:

```bash
sudo bash /tmp/migrate_vps_identity.sh
```

**What the script does:**

1. **Backup**: Creates a backup of `.env` and Nginx config in `/opt/migration_backup_<TIMESTAMP>`.
2. **Stop**: Stops Docker containers (`docker compose down`).
3. **Move**: Renames `/opt/dhamma-channel-automation` to `/opt/flowbiz-client-dhamma`.
4. **Git**: Updates remote URL and pulls the latest code (`main` branch).
5. **Env**: Updates `APP_SERVICE_NAME` and `APP_NAME` in `.env`.
6. **Nginx**: Renames config file, updates upstreams/logs, and reloads Nginx.
7. **Start**: Starts Docker containers again.
8. **Verify**: Checks the `/healthz` endpoint.

### 4. Verification

After the script completes, verify manually:

```bash
# Check directory
ls -la /opt/flowbiz-client-dhamma

# Check service health
curl http://127.0.0.1:3007/healthz

# Check Nginx logs (should be empty/new)
ls -la /var/log/nginx/flowbiz-dhamma-access.log
```

---

## 🔄 Rollback (If needed)

If the migration fails and the script doesn't auto-recover, follow these manual steps:

1. **Stop Services**: `docker compose down`
2. **Rename Back**: `mv /opt/flowbiz-client-dhamma /opt/dhamma-channel-automation`
3. **Restore Configs**:
    * Copy `.env` from backup folder.
    * Restore old Nginx config from backup folder to `/etc/nginx/sites-available/`.
4. **Restore Nginx Symlink**:
    * `ln -sf /etc/nginx/sites-available/dhamma-automation.conf /etc/nginx/sites-enabled/`
    * `rm /etc/nginx/sites-enabled/flowbiz-client-dhamma.conf`
5. **Reload**: `systemctl reload nginx`
6. **Start**: `docker compose up -d`

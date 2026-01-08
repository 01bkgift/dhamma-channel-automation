#!/bin/bash
set -euo pipefail

# -----------------------------------------------------------------------------
# Script: setup_vps_initial.sh
# Purpose: Automate the "One-Time Setup" for FlowBiz VPS deployment.
# Usage:   ./scripts/setup_vps_initial.sh <VPS_USER> <VPS_HOST> [SSH_PORT]
# Example: ./scripts/setup_vps_initial.sh myuser 1.2.3.4 22
# -----------------------------------------------------------------------------

if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <VPS_USER> <VPS_HOST> [SSH_PORT]"
    exit 1
fi

VPS_USER="$1"
VPS_HOST="$2"
SSH_PORT="${3:-22}"

REPO_URL="https://github.com/01bkgift/flowbiz-client-dhamma.git"
TARGET_DIR="/opt/flowbiz-client-dhamma"

echo "--- VPS INITIAL SETUP ---"
echo "Target: $VPS_USER@$VPS_HOST:$SSH_PORT"
echo "Repo:   $REPO_URL"
echo "Dir:    $TARGET_DIR"
echo "-------------------------"

read -p "Are you sure you want to proceed? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# SSH Command Wrapper
ssh_args=(-p "$SSH_PORT" -o StrictHostKeyChecking=accept-new)
run_remote() {
    ssh "${ssh_args[@]}" "$VPS_USER@$VPS_HOST" "bash -s" <<EOF
        set -euo pipefail
        
        echo ">> [Remote] Checking directory..."
        if [ -d "$TARGET_DIR" ]; then
            echo "   Directory $TARGET_DIR already exists."
        else
            echo "   Creating $TARGET_DIR..."
            sudo mkdir -p "$TARGET_DIR"
        fi

        echo ">> [Remote] Checking git repository..."
        if [ -d "$TARGET_DIR/.git" ]; then
            echo "   Repository already cloned."
        else
            echo "   Cloning repository..."
            # Clone into a temp dir first or ensure empty? 
            # We'll try cloning directly. If dir exists and not empty, git clone fails.
            
            # Case 1: Directory created above, empty -> Clone works
            # Case 2: Directory existed, might have stuff.
            
            if [ -z "\$(ls -A $TARGET_DIR)" ]; then
                 sudo git clone "$REPO_URL" "$TARGET_DIR"
            else
                 echo "   WARNING: Target directory is not empty. Attempting to init and pull..."
                 # Safe fallback for existing non-git dirs is complex. Let's assume standard path.
                 # If it fails, user must intervene.
                 cd "$TARGET_DIR"
                 if [ ! -d ".git" ]; then
                    echo "   ERROR: Directory not empty and not a git repo. Manual intervention required."
                    exit 1
                 fi
            fi
        fi

        echo ">> [Remote] Setting permissions..."
        # Ensure the user owns the directory
        sudo chown -R \$(whoami):\$(whoami) "$TARGET_DIR"

        echo ">> [Remote] Setting up .env..."
        cd "$TARGET_DIR"
        if [ ! -f ".env" ]; then
            echo "   Creating .env from .env.example..."
            if [ -f ".env.example" ]; then
                cp .env.example .env
                echo "   IMPORTANT: Don't forget to edit .env with real secrets!"
            else
                echo "   WARNING: .env.example not found."
            fi
        else
            echo "   .env already exists. Skipping."
        fi
        
        echo ">> [Remote] Quick config check..."
        if [ -f "config/flowbiz_port.env" ]; then
            grep FLOWBIZ_ALLOCATED_PORT config/flowbiz_port.env
        else
            echo "   WARNING: config/flowbiz_port.env not found."
        fi

        echo ">> [Remote] Setup Complete!"
EOF
}

echo "Connecting to VPS..."
run_remote

echo "--- DONE ---"
echo "Next steps:"
echo "1. SSH into VPS: ssh -p $SSH_PORT $VPS_USER@$VPS_HOST"
echo "2. Edit .env:    nano $TARGET_DIR/.env"
echo "3. Update Nginx: Follow runbook section 4.6"

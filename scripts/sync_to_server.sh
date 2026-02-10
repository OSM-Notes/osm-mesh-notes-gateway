#!/bin/bash
# Script to sync changes to server and clean untracked files
# Usage: ./scripts/sync_to_server.sh [server_ip]

SERVER="${1:-192.168.2.121}"
REPO_DIR="/home/angoca/LoRa-Meshtastic-OSM-notes-bot"

echo "Syncing repository to server $SERVER..."

# Check if server is reachable
if ! ssh angoca@$SERVER "echo 'Connection test'" 2>/dev/null; then
    echo "Error: Cannot connect to server $SERVER"
    echo "Please ensure the server is online and accessible"
    exit 1
fi

# Show current status
echo "Current git status on server:"
ssh angoca@$SERVER "cd $REPO_DIR && git status --short"

# Show untracked files before cleaning
echo ""
echo "Untracked files (will be removed):"
ssh angoca@$SERVER "cd $REPO_DIR && git ls-files --others --exclude-standard"

# Pull latest changes from git (hard reset to match remote exactly)
echo ""
echo "Pulling latest changes from git..."
ssh angoca@$SERVER "cd $REPO_DIR && git fetch origin && git reset --hard origin/main && git clean -fd"

# Verify no untracked files remain (except .mo files which are generated)
echo ""
echo "Verifying cleanup..."
ssh angoca@$SERVER "cd $REPO_DIR && git status --short"

# Restart service
echo ""
echo "Restarting service..."
ssh angoca@$SERVER "sudo systemctl restart lora-osmnotes"

# Wait a moment and check status
sleep 3
echo ""
echo "Service status:"
ssh angoca@$SERVER "sudo systemctl status lora-osmnotes | head -15"

echo ""
echo "Done!"

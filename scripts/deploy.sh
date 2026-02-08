#!/bin/bash
# Script to deploy updated code to Raspberry Pi server

set -e

# Configuration - UPDATE THESE VALUES
SERVER_USER="${SERVER_USER:-angoca}"
SERVER_HOST="${SERVER_HOST:-raspberrypi}"
SERVER_PATH="${SERVER_PATH:-/home/angoca/LoRa-Meshtastic-OSM-notes-bot}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Deploying code to server...${NC}"
echo "Server: ${SERVER_USER}@${SERVER_HOST}"
echo "Path: ${SERVER_PATH}"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Files to copy
FILES_TO_COPY=(
    "src/gateway/commands.py"
    "locale/es/LC_MESSAGES/lora-osmnotes.po"
    "locale/es/LC_MESSAGES/lora-osmnotes.mo"
    "locale/en/LC_MESSAGES/lora-osmnotes.po"
    "locale/en/LC_MESSAGES/lora-osmnotes.mo"
)

echo -e "${YELLOW}Copying files...${NC}"
for file in "${FILES_TO_COPY[@]}"; do
    local_file="${PROJECT_DIR}/${file}"
    remote_file="${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/${file}"
    
    if [ ! -f "$local_file" ]; then
        echo -e "${RED}Warning: File not found: $local_file${NC}"
        continue
    fi
    
    echo "  Copying: $file"
    scp "$local_file" "$remote_file" || {
        echo -e "${RED}Error copying $file${NC}"
        exit 1
    }
done

echo ""
echo -e "${YELLOW}Recompiling translations on server...${NC}"
ssh "${SERVER_USER}@${SERVER_HOST}" "cd ${SERVER_PATH} && bash scripts/compile_translations.sh" || {
    echo -e "${RED}Error recompiling translations${NC}"
    exit 1
}

echo ""
echo -e "${YELLOW}Restarting service...${NC}"
ssh "${SERVER_USER}@${SERVER_HOST}" "sudo systemctl restart lora-osmnotes" || {
    echo -e "${RED}Error restarting service${NC}"
    exit 1
}

echo ""
echo -e "${GREEN}Deployment complete!${NC}"
echo ""
echo "To check logs:"
echo "  ssh ${SERVER_USER}@${SERVER_HOST} 'sudo journalctl -u lora-osmnotes -f'"

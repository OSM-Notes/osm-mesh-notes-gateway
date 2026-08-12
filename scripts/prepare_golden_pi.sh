#!/bin/bash
# Prepare a "golden" Raspberry Pi for SD image capture.
# Run ON the Pi as root, from a git checkout of this repo.
#
# Manual steps BEFORE this script:
#   1. Flash Raspberry Pi OS to a microSD and boot the Pi
#   2. git clone (or checkout a release tag) this repository
#
# This script (defaults aimed at low-admin field images):
#   - runs install_pi.sh
#   - installs the daily backup timer (systemd, not cron) unless --no-backup-timer
#   - enables lora-osmnotes on boot (auto-start after power loss)
#   - writes IMAGE_INFO.txt under /var/lib/lora-osmnotes
#   - leaves the service stopped while imaging (starts automatically on next boot)
#
# Usage:
#   sudo bash scripts/prepare_golden_pi.sh
#   sudo bash scripts/prepare_golden_pi.sh --tag v0.2.0
#   sudo bash scripts/prepare_golden_pi.sh --no-backup-timer
#   sudo bash scripts/prepare_golden_pi.sh --start-service   # only if Meshtastic is plugged in
#
# After this script: shut down the Pi, move the microSD to a PC, run build_sd_image.sh

set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root: sudo bash $0" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DATA_DIR="${DATA_DIR:-/var/lib/lora-osmnotes}"
TAG=""
WITH_BACKUP_TIMER=1
START_SERVICE=0
DRY_RUN_DEFAULT="false"

while [ $# -gt 0 ]; do
  case "$1" in
    --tag)
      TAG="${2:-}"
      shift 2
      ;;
    --with-backup-timer)
      WITH_BACKUP_TIMER=1
      shift
      ;;
    --no-backup-timer)
      WITH_BACKUP_TIMER=0
      shift
      ;;
    --start-service)
      START_SERVICE=1
      shift
      ;;
    --dry-run-default)
      DRY_RUN_DEFAULT="true"
      shift
      ;;
    -h|--help)
      sed -n '2,28p' "$0" | sed 's/^# \?//'
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 2
      ;;
  esac
done

cd "$PROJECT_DIR"

if [ -n "$TAG" ]; then
  echo "Checking out tag $TAG ..."
  git fetch --tags 2>/dev/null || true
  git checkout "$TAG"
fi

VERSION="$(git describe --tags --always --dirty 2>/dev/null || echo unknown)"
COMMIT="$(git rev-parse HEAD 2>/dev/null || echo unknown)"

echo "=== Preparing golden Pi ==="
echo "Project: $PROJECT_DIR"
echo "Version: $VERSION"
echo "Commit:  $COMMIT"
echo ""

echo ">>> Running install_pi.sh"
bash "$SCRIPT_DIR/install_pi.sh"

if [ "$WITH_BACKUP_TIMER" -eq 1 ]; then
  echo ">>> Installing backup timer"
  bash "$SCRIPT_DIR/install_backup_timer.sh"
fi

# Ensure .env exists with safe defaults for a distributable image
if [ ! -f "$DATA_DIR/.env" ]; then
  cp "$PROJECT_DIR/.env.example" "$DATA_DIR/.env"
fi
# Do not bake secrets; keep SERIAL_PORT default and DRY_RUN as requested
if grep -q '^DRY_RUN=' "$DATA_DIR/.env" 2>/dev/null; then
  sed -i "s/^DRY_RUN=.*/DRY_RUN=$DRY_RUN_DEFAULT/" "$DATA_DIR/.env"
else
  echo "DRY_RUN=$DRY_RUN_DEFAULT" >> "$DATA_DIR/.env"
fi

# Clear live DB so the image ships empty (operators start clean)
if [ -f "$DATA_DIR/gateway.db" ]; then
  echo ">>> Removing live gateway.db from image (clean slate)"
  systemctl stop lora-osmnotes 2>/dev/null || true
  rm -f "$DATA_DIR/gateway.db" "$DATA_DIR/gateway.db-wal" "$DATA_DIR/gateway.db-shm"
fi
rm -rf "$DATA_DIR/backups"/* "$DATA_DIR/exports"/* "$DATA_DIR/reports"/* 2>/dev/null || true

cat > "$DATA_DIR/IMAGE_INFO.txt" <<EOF
OSM Mesh Notes Gateway — golden image metadata
==============================================
Built:   $(date -Is 2>/dev/null || date)
Version: $VERSION
Commit:  $COMMIT
Host:    $(hostname 2>/dev/null || echo unknown)

What starts automatically (no SSH needed):
  - lora-osmnotes.service on every boot (systemd)
  - daily DB backup timer (if installed): keeps last 14 copies under backups/
  - after power loss: Pi boots → gateway comes back → pending notes retry when online

What YOU still must do once (hardware / site):
  1. Plug Heltec (or Meshtastic USB) into the Pi
  2. Give the Pi Internet when you want notes to reach OSM (WiFi/hotspot/Ethernet)
  3. If serial is not /dev/ttyACM0, edit /var/lib/lora-osmnotes/.env SERIAL_PORT=...
  4. Set TZ if needed (default America/Bogota)
  5. Configure field T-Echo nodes to the same LoRa region as the gateway (default ANZ for Colombia)
  6. From Meshtastic: send #osmstatus

Optional ops scripts on this image:
  /var/lib/lora-osmnotes/scripts/health_check.sh
  /var/lib/lora-osmnotes/scripts/mission_report.sh
  /var/lib/lora-osmnotes/scripts/export_notes.sh
  /var/lib/lora-osmnotes/scripts/backup_db.sh
EOF

# Copy ops scripts into data dir for operators without the git tree
mkdir -p "$DATA_DIR/scripts"
for s in health_check.sh mission_report.sh export_notes.sh backup_db.sh; do
  if [ -f "$SCRIPT_DIR/$s" ]; then
    cp -f "$SCRIPT_DIR/$s" "$DATA_DIR/scripts/$s"
    chmod 755 "$DATA_DIR/scripts/$s"
  fi
done

systemctl daemon-reload
systemctl enable lora-osmnotes.service
if [ "$START_SERVICE" -eq 1 ]; then
  systemctl start lora-osmnotes.service
  echo "Service started."
else
  systemctl stop lora-osmnotes.service 2>/dev/null || true
  echo "Service enabled but stopped (good for imaging)."
fi

echo ""
echo "=== Golden Pi ready ==="
echo "Metadata: $DATA_DIR/IMAGE_INFO.txt"
echo ""
echo "Next:"
echo "  1. sudo shutdown -h now"
echo "  2. Move the microSD to a Linux PC"
echo "  3. On the PC: sudo bash scripts/build_sd_image.sh --device /dev/sdX --version $VERSION"
echo "     (replace sdX carefully — wrong device destroys data)"
echo ""

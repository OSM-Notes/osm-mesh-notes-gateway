#!/bin/bash
# Install daily DB backup timer (optional resilience for field gateways).
# Usage: sudo bash scripts/install_backup_timer.sh
#
# Copies backup_db.sh to /var/lib/lora-osmnotes/scripts/ and enables the systemd timer.

set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root: sudo bash $0" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DATA_DIR="${DATA_DIR:-/var/lib/lora-osmnotes}"
DEST_SCRIPTS="$DATA_DIR/scripts"

mkdir -p "$DEST_SCRIPTS" "$DATA_DIR/backups" "$DATA_DIR/exports" "$DATA_DIR/reports"
cp -f "$SCRIPT_DIR/backup_db.sh" "$DEST_SCRIPTS/backup_db.sh"
cp -f "$SCRIPT_DIR/mission_report.sh" "$DEST_SCRIPTS/mission_report.sh"
cp -f "$SCRIPT_DIR/export_notes.sh" "$DEST_SCRIPTS/export_notes.sh"
cp -f "$SCRIPT_DIR/health_check.sh" "$DEST_SCRIPTS/health_check.sh"
chmod 755 "$DEST_SCRIPTS"/*.sh

# High-level note for operators finding the folder on another machine
cat > "$DATA_DIR/README-BACKUP.txt" <<'EOF'
OSM Mesh Notes Gateway — data directory
=======================================

gateway.db     Live SQLite database (notes queue + GPS cache)
backups/       Automatic and manual DB snapshots (gateway-YYYYMMDD-HHMMSS.db)
exports/       CSV/JSON exports from export_notes.sh
reports/       Text reports from mission_report.sh

To recover after SD problems: copy the newest file from backups/ onto a
replacement Pi at /var/lib/lora-osmnotes/gateway.db (stop the service first).

Optional USB: bash scripts/backup_db.sh --usb /media/YOUR_USB
EOF

cp -f "$PROJECT_DIR/systemd/lora-osmnotes-backup.service" /etc/systemd/system/
cp -f "$PROJECT_DIR/systemd/lora-osmnotes-backup.timer" /etc/systemd/system/

systemctl daemon-reload
systemctl enable --now lora-osmnotes-backup.timer

echo "Installed:"
echo "  Scripts → $DEST_SCRIPTS"
echo "  Backups → $DATA_DIR/backups"
echo "  Timer   → lora-osmnotes-backup.timer (daily)"
echo ""
echo "Test now:  sudo systemctl start lora-osmnotes-backup.service"
echo "Status:    systemctl list-timers | grep lora-osmnotes"
echo "Manual:    bash $DEST_SCRIPTS/backup_db.sh"

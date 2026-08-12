#!/bin/bash
# Backup gateway SQLite DB to an easy-to-find directory (and optional USB).
#
# Default destination: /var/lib/lora-osmnotes/backups/
# Optional second copy: set BACKUP_USB_DIR or pass --usb /media/usb
#
# Usage:
#   bash scripts/backup_db.sh
#   bash scripts/backup_db.sh --usb /media/pi/USB_DISK
#   BACKUP_KEEP=14 bash scripts/backup_db.sh
#
# Safe online backup via sqlite3 .backup when possible (service can keep running).

set -u

DATA_DIR="${DATA_DIR:-/var/lib/lora-osmnotes}"
DB_PATH="${DB_PATH:-$DATA_DIR/gateway.db}"
BACKUP_DIR="${BACKUP_DIR:-$DATA_DIR/backups}"
BACKUP_USB_DIR="${BACKUP_USB_DIR:-}"
BACKUP_KEEP="${BACKUP_KEEP:-14}"
USB_DIR=""

while [ $# -gt 0 ]; do
  case "$1" in
    --usb)
      USB_DIR="${2:-}"
      shift 2
      ;;
    --dir)
      BACKUP_DIR="${2:-}"
      shift 2
      ;;
    --db)
      DB_PATH="${2:-}"
      shift 2
      ;;
    --keep)
      BACKUP_KEEP="${2:-14}"
      shift 2
      ;;
    -h|--help)
      cat <<'EOF'
Usage: backup_db.sh [--dir DIR] [--usb DIR] [--keep N] [--db PATH]

Writes: DIR/gateway-YYYYMMDD-HHMMSS.db
Also copies to --usb or BACKUP_USB_DIR when that path exists.
Prunes older backups in DIR keeping the newest N (default 14).
EOF
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 2
      ;;
  esac
done

if [ -n "${BACKUP_USB_DIR}" ] && [ -z "$USB_DIR" ]; then
  USB_DIR="$BACKUP_USB_DIR"
fi

if [ ! -f "$DB_PATH" ]; then
  echo "ERROR: database not found: $DB_PATH" >&2
  exit 1
fi

mkdir -p "$BACKUP_DIR"
STAMP=$(date +%Y%m%d-%H%M%S)
DEST="$BACKUP_DIR/gateway-${STAMP}.db"

copy_db() {
  local target="$1"
  if command -v sqlite3 >/dev/null 2>&1; then
    # Consistent snapshot without stopping the gateway
    if command -v sudo >/dev/null 2>&1 && [ ! -r "$DB_PATH" ]; then
      sudo sqlite3 "$DB_PATH" ".backup '$target'"
      sudo chown "$(id -u):$(id -g)" "$target" 2>/dev/null || true
    else
      sqlite3 "$DB_PATH" ".backup '$target'"
    fi
  else
    # Fallback: stop service briefly for a cold copy
    if command -v systemctl >/dev/null 2>&1 && systemctl is-active --quiet lora-osmnotes 2>/dev/null; then
      sudo systemctl stop lora-osmnotes
      sudo cp "$DB_PATH" "$target"
      sudo systemctl start lora-osmnotes
    else
      cp "$DB_PATH" "$target"
    fi
  fi
}

echo "Backing up $DB_PATH → $DEST"
copy_db "$DEST"
ls -lh "$DEST"

# Optional USB / external path
if [ -n "$USB_DIR" ]; then
  if [ -d "$USB_DIR" ]; then
    mkdir -p "$USB_DIR/lora-osmnotes-backups"
    USB_DEST="$USB_DIR/lora-osmnotes-backups/gateway-${STAMP}.db"
    cp "$DEST" "$USB_DEST"
    echo "Also copied → $USB_DEST"
  else
    echo "WARN: USB path not mounted: $USB_DIR (skipped)"
  fi
fi

# Prune old backups in primary dir
if [ -d "$BACKUP_DIR" ]; then
  # shellcheck disable=SC2012
  ls -1t "$BACKUP_DIR"/gateway-*.db 2>/dev/null | tail -n +"$((BACKUP_KEEP + 1))" | while read -r old; do
    rm -f "$old"
    echo "Pruned old backup: $old"
  done
fi

echo ""
echo "Primary backups live in: $BACKUP_DIR"
echo "To copy to another machine: scp or pull the .db files from that folder (or the USB)."
echo "Done."

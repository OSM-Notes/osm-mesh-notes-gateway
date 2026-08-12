#!/bin/bash
# Export notes table to CSV or JSON for post-mission archive.
# Invoked manually (coordinator with SSH/console access).
#
# Usage:
#   bash scripts/export_notes.sh
#   bash scripts/export_notes.sh --out /var/lib/lora-osmnotes/exports/notes.csv
#   bash scripts/export_notes.sh --format json --out /tmp/notes.json
#   bash scripts/export_notes.sh --status pending
#
# Default output: /var/lib/lora-osmnotes/exports/notes-YYYYMMDD-HHMMSS.csv

set -u

DATA_DIR="${DATA_DIR:-/var/lib/lora-osmnotes}"
DB_PATH="${DB_PATH:-$DATA_DIR/gateway.db}"
FORMAT="csv"
STATUS=""
OUT=""

while [ $# -gt 0 ]; do
  case "$1" in
    --out|-o)
      OUT="${2:-}"
      shift 2
      ;;
    --format|-f)
      FORMAT="${2:-csv}"
      shift 2
      ;;
    --status)
      STATUS="${2:-}"
      shift 2
      ;;
    --db)
      DB_PATH="${2:-}"
      shift 2
      ;;
    -h|--help)
      cat <<'EOF'
Usage: export_notes.sh [--out FILE] [--format csv|json] [--status pending|sent] [--db PATH]

Default directory: /var/lib/lora-osmnotes/exports/
Review text_original for personal data before sharing.
EOF
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 2
      ;;
  esac
done

if ! command -v sqlite3 >/dev/null 2>&1; then
  echo "ERROR: sqlite3 CLI is not installed (apt install sqlite3)" >&2
  exit 1
fi

if [ ! -f "$DB_PATH" ]; then
  echo "ERROR: database not found: $DB_PATH" >&2
  exit 1
fi

FORMAT=$(echo "$FORMAT" | tr '[:upper:]' '[:lower:]')
if [ "$FORMAT" != "csv" ] && [ "$FORMAT" != "json" ]; then
  echo "ERROR: --format must be csv or json" >&2
  exit 2
fi

STAMP=$(date +%Y%m%d-%H%M%S)
if [ -z "$OUT" ]; then
  mkdir -p "$DATA_DIR/exports"
  OUT="$DATA_DIR/exports/notes-${STAMP}.${FORMAT}"
fi

mkdir -p "$(dirname "$OUT")"

WHERE="1=1"
if [ -n "$STATUS" ]; then
  WHERE="status = '$(echo "$STATUS" | sed "s/'/''/g")'"
fi

sqlite_cmd() {
  if command -v sudo >/dev/null 2>&1 && [ ! -r "$DB_PATH" ]; then
    sudo sqlite3 "$DB_PATH" "$@"
  else
    sqlite3 "$DB_PATH" "$@"
  fi
}

COLS="id, local_queue_id, node_id, created_at, lat, lon, text_original, text_normalized, status, osm_note_id, osm_note_url, sent_at, last_error, notified_sent"

if [ "$FORMAT" = "csv" ]; then
  sqlite_cmd -header -csv "SELECT $COLS FROM notes WHERE $WHERE ORDER BY id ASC;" > "$OUT"
else
  # JSON array via sqlite json if available; fallback to line-oriented objects
  if sqlite_cmd "SELECT json_array();" >/dev/null 2>&1; then
    sqlite_cmd \
      "SELECT json_group_array(json_object(
        'id', id,
        'local_queue_id', local_queue_id,
        'node_id', node_id,
        'created_at', created_at,
        'lat', lat,
        'lon', lon,
        'text_original', text_original,
        'text_normalized', text_normalized,
        'status', status,
        'osm_note_id', osm_note_id,
        'osm_note_url', osm_note_url,
        'sent_at', sent_at,
        'last_error', last_error,
        'notified_sent', notified_sent
      )) FROM notes WHERE $WHERE;" > "$OUT"
  else
    echo "ERROR: this sqlite3 build cannot emit JSON objects" >&2
    exit 1
  fi
fi

COUNT=$(sqlite_cmd "SELECT COUNT(*) FROM notes WHERE $WHERE;")
echo "Exported $COUNT note(s) → $OUT"
echo "WARNING: Review text_original for personal data before sharing with third parties."

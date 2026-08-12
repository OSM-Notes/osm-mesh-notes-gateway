#!/bin/bash
# Mission / daily operational report for OSM Mesh Notes Gateway.
# Invoked manually by a coordinator (SSH or local console), e.g. end of day.
#
# Usage:
#   bash scripts/mission_report.sh
#   bash scripts/mission_report.sh --out /var/lib/lora-osmnotes/reports/mission.txt

set -u

DATA_DIR="${DATA_DIR:-/var/lib/lora-osmnotes}"
DB_PATH="${DB_PATH:-$DATA_DIR/gateway.db}"
OUT=""

while [ $# -gt 0 ]; do
  case "$1" in
    --out|-o) OUT="${2:-}"; shift 2 ;;
    --db) DB_PATH="${2:-}"; shift 2 ;;
    -h|--help) echo "Usage: $0 [--out FILE] [--db PATH]"; exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
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

sqlite_cmd() {
  if command -v sudo >/dev/null 2>&1 && [ ! -r "$DB_PATH" ]; then
    sudo sqlite3 "$DB_PATH" "$@"
  else
    sqlite3 "$DB_PATH" "$@"
  fi
}

TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

{
  echo "OSM Mesh Notes Gateway — mission report"
  echo "Generated: $(date -Is 2>/dev/null || date)"
  echo "Database:  $DB_PATH"
  echo ""

  TOTAL=$(sqlite_cmd "SELECT COUNT(*) FROM notes;" 2>/dev/null || echo "?")
  PENDING=$(sqlite_cmd "SELECT COUNT(*) FROM notes WHERE status='pending';" 2>/dev/null || echo "?")
  SENT=$(sqlite_cmd "SELECT COUNT(*) FROM notes WHERE status='sent';" 2>/dev/null || echo "?")
  WITH_ERR=$(sqlite_cmd "SELECT COUNT(*) FROM notes WHERE last_error IS NOT NULL AND last_error != '';" 2>/dev/null || echo "?")
  SENT_TODAY=$(sqlite_cmd "SELECT COUNT(*) FROM notes WHERE status='sent' AND date(sent_at) = date('now');" 2>/dev/null || echo "?")
  CREATED_TODAY=$(sqlite_cmd "SELECT COUNT(*) FROM notes WHERE date(created_at) = date('now');" 2>/dev/null || echo "?")
  LAST_SENT=$(sqlite_cmd "SELECT local_queue_id || ' @ ' || IFNULL(sent_at,'?') || ' → #' || IFNULL(osm_note_id,'?') FROM notes WHERE status='sent' ORDER BY sent_at DESC LIMIT 1;" 2>/dev/null || echo "(none)")

  echo "=== Summary ==="
  echo "Total notes:        $TOTAL"
  echo "  pending:          $PENDING"
  echo "  sent:             $SENT"
  echo "  with last_error:  $WITH_ERR"
  echo "Created today (UTC date in DB): $CREATED_TODAY"
  echo "Sent today (UTC date in DB):    $SENT_TODAY"
  echo "Local calendar date:            $(date +%Y-%m-%d)"
  echo "Last successful send: $LAST_SENT"
  echo ""

  echo "=== Pending queue (max 30) ==="
  PENDING_ROWS=$(sqlite_cmd -header -column \
    "SELECT local_queue_id, node_id, substr(text_original,1,40) AS text, created_at, substr(IFNULL(last_error,''),1,40) AS err
     FROM notes WHERE status='pending' ORDER BY created_at ASC LIMIT 30;" 2>/dev/null || true)
  if [ -z "${PENDING_ROWS:-}" ]; then echo "(empty)"; else echo "$PENDING_ROWS"; fi
  echo ""

  echo "=== Last 10 sent ==="
  SENT_ROWS=$(sqlite_cmd -header -column \
    "SELECT local_queue_id, osm_note_id, sent_at, substr(text_original,1,40) AS text
     FROM notes WHERE status='sent' ORDER BY sent_at DESC LIMIT 10;" 2>/dev/null || true)
  if [ -z "${SENT_ROWS:-}" ]; then echo "(none)"; else echo "$SENT_ROWS"; fi
  echo ""

  echo "=== Recent service log hints (journal, last 24h) ==="
  if command -v journalctl >/dev/null 2>&1; then
    MATCH=$(journalctl -u lora-osmnotes --since "24 hours ago" --no-pager 2>/dev/null \
      | grep -iE 'error|sent |Created note|Marked note|Max retries' | tail -n 15 || true)
    if [ -z "$MATCH" ]; then echo "(no matching lines)"; else echo "$MATCH"; fi
  else
    echo "(journalctl not available)"
  fi
  echo ""

  echo "=== Next steps ==="
  echo "- Export CSV:  bash scripts/export_notes.sh"
  echo "- Backup DB:   bash scripts/backup_db.sh"
  echo "- Health:      bash scripts/health_check.sh"
  echo ""
  echo "Privacy: review text_original before sharing exports with third parties."
} > "$TMP"

cat "$TMP"
if [ -n "$OUT" ]; then
  mkdir -p "$(dirname "$OUT")"
  cp "$TMP" "$OUT"
  echo ""
  echo "Saved → $OUT"
fi

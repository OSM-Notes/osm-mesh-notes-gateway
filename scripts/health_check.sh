#!/bin/bash
# Operational health check for OSM Mesh Notes Gateway (humanitarian field use).
# Usage: bash scripts/health_check.sh
# Exit 0 = healthy enough to operate; non-zero = attention required.

set -u

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

OK=0
WARN=0
FAIL=0

pass() { echo -e "  ${GREEN}OK${NC}  $1"; OK=$((OK + 1)); }
warn() { echo -e "  ${YELLOW}WARN${NC} $1"; WARN=$((WARN + 1)); }
fail() { echo -e "  ${RED}FAIL${NC} $1"; FAIL=$((FAIL + 1)); }

DATA_DIR="${DATA_DIR:-/var/lib/lora-osmnotes}"
DB_PATH="${DATA_DIR}/gateway.db"
ENV_FILE="${DATA_DIR}/.env"
SERVICE_NAME="lora-osmnotes"

echo "OSM Mesh Notes Gateway — health check"
echo "Time: $(date -Is 2>/dev/null || date)"
echo ""

# --- systemd ---
echo "Service"
if command -v systemctl >/dev/null 2>&1; then
  if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
    pass "systemd unit ${SERVICE_NAME} is active"
  else
    fail "systemd unit ${SERVICE_NAME} is not active (systemctl status ${SERVICE_NAME})"
  fi
  if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
    pass "systemd unit enabled on boot"
  else
    warn "systemd unit not enabled on boot"
  fi
else
  warn "systemctl not available (not checking service)"
fi
echo ""

# --- config ---
echo "Configuration"
if [ -f "$ENV_FILE" ]; then
  pass "env file present: $ENV_FILE"
  # shellcheck disable=SC1090
  set -a
  # Prefer parsing SERIAL_PORT without sourcing arbitrary shell
  SERIAL_PORT=$(grep -E '^[[:space:]]*SERIAL_PORT=' "$ENV_FILE" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '"' | tr -d "'")
  DRY_RUN=$(grep -E '^[[:space:]]*DRY_RUN=' "$ENV_FILE" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '"' | tr -d "'" | tr '[:upper:]' '[:lower:]')
  set +a
  SERIAL_PORT="${SERIAL_PORT:-/dev/ttyACM0}"
  if [ "${DRY_RUN}" = "true" ]; then
    warn "DRY_RUN=true (training mode — notes are not sent to OSM)"
  else
    pass "DRY_RUN is not true (production-style send enabled)"
  fi
else
  warn "no env file at $ENV_FILE (using defaults)"
  SERIAL_PORT="/dev/ttyACM0"
fi
echo ""

# --- serial ---
echo "Serial / Meshtastic"
if [ -e "$SERIAL_PORT" ]; then
  pass "serial device exists: $SERIAL_PORT"
  if [ -r "$SERIAL_PORT" ] && [ -w "$SERIAL_PORT" ]; then
    pass "serial device readable/writable by $(id -un)"
  else
    fail "no read/write on $SERIAL_PORT (add user to dialout and re-login)"
  fi
else
  fail "serial device missing: $SERIAL_PORT (run scripts/detect_serial.sh)"
fi
echo ""

# --- disk ---
echo "Disk"
if [ -d "$DATA_DIR" ]; then
  pass "data dir exists: $DATA_DIR"
  AVAIL_KB=$(df -k "$DATA_DIR" 2>/dev/null | awk 'NR==2 {print $4}')
  if [ -n "${AVAIL_KB:-}" ]; then
    AVAIL_MB=$((AVAIL_KB / 1024))
    if [ "$AVAIL_MB" -lt 100 ]; then
      fail "low disk space: ${AVAIL_MB} MB free"
    elif [ "$AVAIL_MB" -lt 500 ]; then
      warn "disk space low: ${AVAIL_MB} MB free"
    else
      pass "disk space: ${AVAIL_MB} MB free"
    fi
  fi
else
  fail "data dir missing: $DATA_DIR"
fi
echo ""

# --- database / queue ---
echo "Queue (SQLite)"
if [ -f "$DB_PATH" ]; then
  pass "database present: $DB_PATH"
  if command -v sqlite3 >/dev/null 2>&1; then
    PENDING=$(sudo sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM notes WHERE status='pending';" 2>/dev/null \
      || sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM notes WHERE status='pending';" 2>/dev/null \
      || echo "")
    TOTAL=$(sudo sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM notes;" 2>/dev/null \
      || sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM notes;" 2>/dev/null \
      || echo "")
    if [ -n "$PENDING" ]; then
      if [ "$PENDING" -gt 50 ] 2>/dev/null; then
        warn "pending queue size: $PENDING (check Internet / OSM)"
      else
        pass "pending queue size: $PENDING (total notes: ${TOTAL:-?})"
      fi
    else
      warn "could not query notes table (permissions? install sqlite3)"
    fi
  else
    warn "sqlite3 CLI not installed — skip queue counts"
  fi
else
  warn "database not created yet: $DB_PATH (normal before first start)"
fi
echo ""

# --- time / NTP ---
echo "Time"
if command -v timedatectl >/dev/null 2>&1; then
  if timedatectl status 2>/dev/null | grep -q "System clock synchronized: yes"; then
    pass "NTP synchronized"
  else
    warn "NTP not synchronized (see docs/TIME_CONFIGURATION.md)"
  fi
else
  warn "timedatectl not available"
fi
echo ""

# --- network (optional) ---
echo "Network"
if ping -c 1 -W 3 api.openstreetmap.org >/dev/null 2>&1; then
  pass "ping api.openstreetmap.org OK"
elif command -v curl >/dev/null 2>&1 && curl -sI --max-time 5 https://www.openstreetmap.org >/dev/null 2>&1; then
  pass "HTTPS openstreetmap.org reachable"
else
  warn "no reachability to OSM (store-and-forward will queue notes)"
fi
echo ""

# --- recent logs ---
echo "Recent service errors (last 24h, if any)"
if command -v journalctl >/dev/null 2>&1; then
  ERR_COUNT=$(journalctl -u "$SERVICE_NAME" --since "24 hours ago" 2>/dev/null | grep -ciE 'error|exception|failed' || true)
  if [ "${ERR_COUNT}" -eq 0 ]; then
    pass "no error-like lines in last 24h logs"
  else
    warn "found ~${ERR_COUNT} error-like log lines (journalctl -u ${SERVICE_NAME} -p err)"
  fi
else
  warn "journalctl not available"
fi
echo ""

echo "Summary: ${OK} ok, ${WARN} warnings, ${FAIL} failures"
if [ "$FAIL" -gt 0 ]; then
  echo "Result: ATTENTION REQUIRED"
  exit 1
fi
echo "Result: OK TO OPERATE (review warnings if any)"
exit 0

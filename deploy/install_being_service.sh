#!/bin/bash
# BEING _ OMEGA + PRIM E — native launchd service installer
# Installs com.being.omega.prime as a user LaunchAgent (boot-persistent, self-healing).
set -euo pipefail

PLIST_LABEL="com.being.omega.prime"
PLIST_SRC="/Users/jjmarte/delta-stream/qb_protocol/deploy/com.being.omega.prime.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/${PLIST_LABEL}.plist"
LOG_DIR="$HOME/Library/Logs"

mkdir -p "$HOME/Library/LaunchAgents" "$LOG_DIR"

if [ ! -f "$PLIST_SRC" ]; then
  echo "Missing plist source at $PLIST_SRC" >&2
  exit 1
fi

cp "$PLIST_SRC" "$PLIST_DEST"

if launchctl list "$PLIST_LABEL" >/dev/null 2>&1; then
  launchctl bootout gui/$(id -u)/"$PLIST_LABEL" || true
fi

launchctl bootstrap gui/$(id -u) "$PLIST_DEST"
launchctl enable gui/$(id -u)/"$PLIST_LABEL" || true

echo "Installed and started $PLIST_LABEL"
echo "Logs: $LOG_DIR/being_omega_prime.out.log"
echo "Logs: $LOG_DIR/being_omega_prime.err.log"
echo "Status: launchctl list | grep being"

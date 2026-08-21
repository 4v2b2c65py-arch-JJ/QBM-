#!/bin/bash
# BEING _ OMEGA + PRIM E — native launchd service uninstaller
set -euo pipefail

PLIST_LABEL="com.being.omega.prime"
PLIST_DEST="$HOME/Library/LaunchAgents/${PLIST_LABEL}.plist"

if launchctl list "$PLIST_LABEL" >/dev/null 2>&1; then
  launchctl bootout gui/$(id -u)/"$PLIST_LABEL" || true
fi

if [ -f "$PLIST_DEST" ]; then
  rm -f "$PLIST_DEST"
fi

echo "Uninstalled $PLIST_LABEL"

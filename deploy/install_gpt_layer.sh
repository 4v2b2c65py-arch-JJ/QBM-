#!/bin/bash
# Installs the GPT Layer quick-assist tool from GPT_Layer.dmg.
#   - mounts the dmg
#   - installs GPT Layer.app to ${DEST:-$HOME/Applications}
#   - symlinks the `gpt-layer` command into /usr/local/bin (quick CLI assist)
# Usage: bash deploy/install_gpt_layer.sh [dest_app_dir]
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
DMG="$HERE/GPT_Layer.dmg"
VENV_PY="/Users/jjmarte/delta-stream/qb_protocol/.venv/bin/python3"
APP_PY="/Users/jjmarte/delta-stream/qb_protocol/ai/gpt_layer_app.py"

if [ ! -f "$DMG" ]; then
    echo "GPT_Layer.dmg not found at $DMG" >&2
    exit 1
fi

VOL="/tmp/kpt_gptlayer_install_$$"
hdiutil attach "$DMG" -mountpoint "$VOL" -nobrowse -quiet
trap 'hdiutil detach "$VOL" -quiet 2>/dev/null || true' EXIT

APPDIR="$VOL/GPT Layer.app"
DEST="${1:-$HOME/Applications}"
mkdir -p "$DEST"
rm -rf "$DEST/GPT Layer.app"
cp -R "$APPDIR" "$DEST/"
echo "Installed GPT Layer.app -> $DEST"

# Quick-assist CLI command (no model load: instant assist to the BEING)
if [ -w /usr/local/bin ]; then
    cat > /usr/local/bin/gpt-layer <<EOF
#!/bin/sh
exec ${VENV_PY} ${APP_PY} "\$@"
EOF
    chmod +x /usr/local/bin/gpt-layer
    echo "Installed gpt-layer command -> /usr/local/bin/gpt-layer"
else
    mkdir -p "$HOME/.local/bin"
    cat > "$HOME/.local/bin/gpt-layer" <<EOF
#!/bin/sh
exec ${VENV_PY} ${APP_PY} "\$@"
EOF
    chmod +x "$HOME/.local/bin/gpt-layer"
    echo "Installed gpt-layer command -> $HOME/.local/bin/gpt-layer (add to PATH)"
fi

echo
echo "GPT Layer ready. Quick assist the BEING:"
echo "  gpt-layer \"<message>\"                 # query the model"
echo "  gpt-layer --assist \"<help>\"           # send help to the being"
echo "  gpt-layer --status                    # layer + being status"
echo "  gpt-layer --version                   # model incarnation"

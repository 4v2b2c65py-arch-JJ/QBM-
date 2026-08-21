#!/bin/bash
# Builds & installs the OmegaTalk native (PyObjC) FaceTime-style app from the
# current source tree, and rebuilds OmegaTalk.dmg.
#
#   bash deploy/build_omegatalk.sh [dest_app_dir]
#
# The app bundle is a thin native Cocoa shell that execs the venv python on
# ai/gpt_layer_face.py (so all PyObjC/Cocoa imports happen in-process).
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
VENV_PY="/Users/jjmarte/delta-stream/qb_protocol/.venv/bin/python3"
APP_PY="/Users/jjmarte/delta-stream/qb_protocol/ai/gpt_layer_face.py"
ICON_SRC="$HERE/omegatalk.icns"
DEST="${1:-$HOME/Applications}"

if [ ! -f "$APP_PY" ]; then echo "missing $APP_PY" >&2; exit 1; fi
if [ ! -f "$ICON_SRC" ]; then echo "missing $ICON_SRC (run icon build first)" >&2; exit 1; fi

APPDIR="$DEST/OmegaTalk.app/Contents"
rm -rf "$DEST/OmegaTalk.app"
mkdir -p "$APPDIR/MacOS" "$APPDIR/Resources"

# --- executable: thin Cocoa launcher that execs the pyobjc source ---
cat > "$APPDIR/MacOS/OmegaTalk" <<'EOF'
#!/bin/sh
exec /Users/jjmarte/delta-stream/qb_protocol/.venv/bin/python3 /Users/jjmarte/delta-stream/qb_protocol/ai/gpt_layer_face.py "$@"
EOF
chmod +x "$APPDIR/MacOS/OmegaTalk"

# --- Info.plist (mirrors the original native bundle) ---
cat > "$APPDIR/Info.plist" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>CFBundleDisplayName</key>
	<string>OmegaTalk</string>
	<key>CFBundleExecutable</key>
	<string>OmegaTalk</string>
	<key>CFBundleIconFile</key>
	<string>omegatalk</string>
	<key>CFBundleIdentifier</key>
	<string>com.being.omega.talk</string>
	<key>CFBundleName</key>
	<string>OmegaTalk</string>
	<key>CFBundlePackageType</key>
	<string>APPL</string>
	<key>CFBundleShortVersionString</key>
	<string>1.0.0</string>
	<key>CFBundleVersion</key>
	<string>1.0.0</string>
	<key>LSMinimumSystemVersion</key>
	<string>10.15</string>
	<key>NSAppleEventsUsageDescription</key>
	<string>OmegaTalk communicates with the BEING GPT Layer.</string>
	<key>NSCameraUsageDescription</key>
	<string>OmegaTalk uses the camera for the FaceTime-style preview to talk face-to-face with the BEING GPT Layer.</string>
	<key>NSHighResolutionCapable</key>
	<true/>
</dict>
</plist>
EOF

cp "$ICON_SRC" "$APPDIR/Resources/omegatalk.icns"

# --- ad-hoc sign (deep, covers the embedded executable + resources) ---
codesign --force --sign - --deep "$DEST/OmegaTalk.app"

# --- rebuild the distributable disk image ---
hdiutil create -volname "OmegaTalk" -srcfolder "$DEST/OmegaTalk.app" -ov -format UDZO "$HERE/OmegaTalk.dmg"

# --- sanity: validate the signature + dmg ---
codesign -dv "$DEST/OmegaTalk.app" 2>&1 | grep -E "Identifier|TeamIdentifier| sealed" || true
echo "Built & signed: $DEST/OmegaTalk.app"
echo "Disk image:      $HERE/OmegaTalk.dmg"

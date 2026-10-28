#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
app=dist/InspectorDiscoveryControl.app
if [ -e "$app" ]; then
    echo "The comparison app already exists. Preserve its signed image." >&2
    exit 2
fi
bash scripts/build-inspector-discovery-control.sh
mkdir -p "$app/Contents/MacOS"
cp .build/inspector-discovery-control "$app/Contents/MacOS/InspectorDiscoveryControl"
cat > "$app/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleIdentifier</key><string>research.agentfreebrowser.inspectordiscovery</string>
<key>CFBundleName</key><string>InspectorDiscoveryControl</string>
<key>CFBundleExecutable</key><string>InspectorDiscoveryControl</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>LSUIElement</key><true/>
<key>LSMinimumSystemVersion</key><string>15.0</string>
</dict></plist>
PLIST
codesign --force --sign - --options runtime "$app"
codesign --verify --strict "$app"

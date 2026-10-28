#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
name=AgentFreeBrowserPreview
app="dist/$name.app"
if [ -e docs/evidence/integrated-browser-permission-manifest.json ]; then
    echo "The preview consent image is pinned. Use a new identity for a source change." >&2
    exit 2
fi
mkdir -p .build/module-cache "$app/Contents/MacOS"
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library -O \
    -target arm64-apple-macosx15.0 -module-cache-path .build/module-cache \
    -D DEVICE_KEYBOARD_EXPERIMENT -D INTEGRATED_BROWSER \
    Sources/Browser/*.swift -o "$app/Contents/MacOS/$name"
cat > "$app/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<plist version="1.0"><dict>
<key>CFBundleIdentifier</key><string>research.agentfreebrowser.preview</string>
<key>CFBundleName</key><string>$name</string>
<key>CFBundleExecutable</key><string>$name</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>LSMinimumSystemVersion</key><string>15.0</string>
<key>NSHighResolutionCapable</key><true/>
<key>NSInputMonitoringUsageDescription</key><string>Route the built-in keyboard only while this browser has focus. No typed text or key codes enter saved logs.</string>
<key>NSAppTransportSecurity</key><dict><key>NSAllowsLocalNetworking</key><true/></dict>
</dict></plist>
PLIST
codesign --force --sign - --options runtime "$app"
codesign --verify --strict "$app"

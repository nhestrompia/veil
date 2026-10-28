#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
app=dist/DragSource.app
mkdir -p .build/module-cache "$app/Contents/MacOS"
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library -O \
    -target arm64-apple-macosx14.0 -module-cache-path .build/module-cache \
    Sources/Probe/DesktopInputSafety.swift Sources/Diagnostics/DragSource.swift -o "$app/Contents/MacOS/DragSource"
cat > "$app/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<plist version="1.0"><dict>
<key>CFBundleIdentifier</key><string>research.agentfreebrowser.dragsource</string>
<key>CFBundleName</key><string>DragSource</string>
<key>CFBundleExecutable</key><string>DragSource</string>
<key>CFBundlePackageType</key><string>APPL</string>
</dict></plist>
EOF
codesign --force --sign - --options runtime --entitlements config/browser.entitlements "$app"

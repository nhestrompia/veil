#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
app=dist/HIDObservation.app
mkdir -p .build/module-cache "$app/Contents/MacOS"
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library -O \
    -target arm64-apple-macosx14.0 -module-cache-path .build/module-cache \
    Sources/HIDObservation/*.swift -o "$app/Contents/MacOS/HIDObservation"
cat > "$app/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleIdentifier</key><string>research.agentfreebrowser.hidobservation</string>
<key>CFBundleName</key><string>HIDObservation</string>
<key>CFBundleExecutable</key><string>HIDObservation</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>LSMinimumSystemVersion</key><string>14.0</string>
<key>NSInputMonitoringUsageDescription</key><string>Compare device event categories with synthetic input while the research window has focus.</string>
</dict></plist>
EOF
codesign --force --sign - --options runtime "$app"
codesign --verify --strict "$app"

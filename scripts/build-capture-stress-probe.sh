#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
name=CaptureStressProbe
app="dist/$name.app"
if [ -e docs/evidence/capture-stress-permission-manifest.json ]; then
    echo "The consent image is pinned. Build a new helper identity for any source change." >&2
    exit 2
fi
mkdir -p .build/module-cache "$app/Contents/MacOS"
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library -O \
    -target arm64-apple-macosx15.0 -module-cache-path .build/module-cache \
    "$PWD/Sources/Diagnostics/CaptureStressProbe.swift" -o "$app/Contents/MacOS/$name"
cat > "$app/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleIdentifier</key><string>research.agentfreebrowser.capturestress</string>
<key>CFBundleName</key><string>$name</string>
<key>CFBundleExecutable</key><string>$name</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>LSMinimumSystemVersion</key><string>15.0</string>
<key>NSHighResolutionCapable</key><true/>
</dict></plist>
PLIST
codesign --force --sign - --options runtime "$app"
codesign --verify --strict "$app"

#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .build/module-cache
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library -O \
    -module-cache-path .build/module-cache \
    "$PWD/Sources/Diagnostics/RendererProcessScope.swift" \
    "$PWD/Sources/Diagnostics/RendererAXProbe.swift" -o .build/renderer-ax-probe
app=dist/RendererAXProbe.app
mkdir -p "$app/Contents/MacOS"
cp .build/renderer-ax-probe "$app/Contents/MacOS/RendererAXProbe"
cat > "$app/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleIdentifier</key><string>research.agentfreebrowser.rendererprobe</string>
<key>CFBundleName</key><string>RendererAXProbe</string>
<key>CFBundleExecutable</key><string>RendererAXProbe</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>LSUIElement</key><true/>
<key>LSMinimumSystemVersion</key><string>14.0</string>
</dict></plist>
EOF
codesign --force --sign - --options runtime "$app"
codesign --verify --strict "$app"

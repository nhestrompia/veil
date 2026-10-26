#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
app=dist/HeadlessRendererProbe.app
mkdir -p .build/module-cache "$app/Contents/MacOS"
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library -O \
    -module-cache-path .build/module-cache "$PWD/Sources/Diagnostics/HeadlessRendererProbe.swift" \
    -o "$app/Contents/MacOS/HeadlessRendererProbe"
cat > "$app/Contents/Info.plist" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleIdentifier</key><string>research.agentfreebrowser.headlessrendererprobe</string>
<key>CFBundleName</key><string>HeadlessRendererProbe</string>
<key>CFBundleExecutable</key><string>HeadlessRendererProbe</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>LSUIElement</key><true/>
</dict></plist>
EOF
codesign --force --sign - --options runtime "$app"
codesign --verify --strict "$app"

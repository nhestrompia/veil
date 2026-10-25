#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .build/module-cache
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library -O \
    -module-cache-path .build/module-cache Sources/Diagnostics/FakeKeyMatcher.swift Sources/Diagnostics/KeyboardObservationProbe.swift \
    -o .build/keyboard-observation-probe
app=dist/KeyboardObservationProbe.app
mkdir -p "$app/Contents/MacOS"
cp .build/keyboard-observation-probe "$app/Contents/MacOS/KeyboardObservationProbe"
cat > "$app/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleIdentifier</key><string>research.agentfreebrowser.keyboardobserver</string>
<key>CFBundleName</key><string>KeyboardObservationProbe</string>
<key>CFBundleExecutable</key><string>KeyboardObservationProbe</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>LSMinimumSystemVersion</key><string>14.0</string>
<key>LSUIElement</key><true/>
</dict></plist>
EOF
codesign --force --sign - --options runtime "$app"
codesign --verify --strict "$app"

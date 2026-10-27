#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
name=ProtectedLayerExperiment
app="dist/$name.app"
mkdir -p .build/module-cache "$app/Contents/MacOS"
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library -O \
    -target arm64-apple-macosx15.0 -module-cache-path .build/module-cache -D PIXEL_H264 \
    Sources/Rendering/H264Frames.swift Sources/Diagnostics/ProtectedLayerExperiment.swift \
    -o "$app/Contents/MacOS/$name"
cat > "$app/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleIdentifier</key><string>research.agentfreebrowser.$name</string>
<key>CFBundleName</key><string>$name</string>
<key>CFBundleExecutable</key><string>$name</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>LSMinimumSystemVersion</key><string>15.0</string>
<key>NSHighResolutionCapable</key><true/>
</dict></plist>
EOF
codesign --force --sign - --options runtime "$app"
codesign --verify --strict "$app"

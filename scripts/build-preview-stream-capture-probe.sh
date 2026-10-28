#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -e docs/evidence/preview-stream-permission-manifest.json ]; then
    echo "The final consent image is pinned. Do not rebuild or re-sign it." >&2
    exit 2
fi
name=PreviewStreamCaptureProbe
app="dist/$name.app"
mkdir -p .build/module-cache "$app/Contents/MacOS"
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library -O \
    -target arm64-apple-macosx15.0 -module-cache-path .build/module-cache \
    "$PWD/Sources/Diagnostics/RendererProcessScope.swift" \
    "$PWD/Sources/Diagnostics/PreviewAXScope.swift" \
    "$PWD/Sources/Diagnostics/PreviewCapturePixels.swift" \
    "$PWD/Sources/Diagnostics/PreviewStreamCaptureProbe.swift" \
    -o "$app/Contents/MacOS/$name"
cat > "$app/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleIdentifier</key><string>research.agentfreebrowser.previewstreamcapture</string>
<key>CFBundleName</key><string>$name</string>
<key>CFBundleExecutable</key><string>$name</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>LSUIElement</key><true/>
<key>LSMinimumSystemVersion</key><string>15.0</string>
</dict></plist>
PLIST
codesign --force --sign - --options runtime "$app"
codesign --verify --strict "$app"

#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .build/module-cache dist
for variant in protected control nv12protected nv12control; do
    if [ "$variant" = protected ]; then
        name=PixelProtectedExperiment
        defines=(-D PIXEL_PROTECTION)
    elif [ "$variant" = control ]; then
        name=PixelControl
        defines=(-D PIXEL_CONTROL)
    elif [ "$variant" = nv12protected ]; then
        name=PixelNV12ProtectedExperiment
        defines=(-D PIXEL_PROTECTION -D PIXEL_NV12)
    else
        name=PixelNV12Control
        defines=(-D PIXEL_CONTROL -D PIXEL_NV12)
    fi
    app="dist/$name.app"
    mkdir -p "$app/Contents/MacOS"
    xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library -O \
        -target arm64-apple-macosx14.0 -module-cache-path .build/module-cache "${defines[@]}" \
        Sources/Browser/BrowserPolicy.swift Sources/Rendering/*.swift -o "$app/Contents/MacOS/$name"
    cat > "$app/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleIdentifier</key><string>research.agentfreebrowser.$name</string>
<key>CFBundleName</key><string>$name</string>
<key>CFBundleExecutable</key><string>$name</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>LSMinimumSystemVersion</key><string>14.0</string>
<key>NSHighResolutionCapable</key><true/>
<key>NSAppTransportSecurity</key><dict><key>NSAllowsLocalNetworking</key><true/></dict>
</dict></plist>
EOF
    codesign --force --sign - --options runtime --entitlements config/browser.entitlements "$app"
    codesign --verify --strict "$app"
done

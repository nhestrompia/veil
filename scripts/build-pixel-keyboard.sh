#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .build/module-cache dist
for variant in protected control; do
    if [ "$variant" = protected ]; then
        name=PixelKeyboardExperiment
        defines=(-D PIXEL_H264 -D PIXEL_PROTECTION -D PIXEL_KEYBOARD -D DEVICE_KEYBOARD_EXPERIMENT)
    else
        name=PixelKeyboardRoutingControl
        defines=(-D PIXEL_H264 -D PIXEL_CONTROL -D PIXEL_KEYBOARD -D DEVICE_KEYBOARD_EXPERIMENT -D PIXEL_ROUTING_CONTROL)
    fi
    app="dist/$name.app"
    mkdir -p "$app/Contents/MacOS"
    xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library -O \
        -target arm64-apple-macosx15.0 -module-cache-path .build/module-cache "${defines[@]}" \
        Sources/Browser/BrowserPolicy.swift Sources/Browser/BrowserRuntimePolicy.swift \
        Sources/Browser/HIDSourcePolicy.swift Sources/Browser/DeviceKeyboard.swift \
        Sources/Browser/AXBoundary.swift Sources/Browser/RestrictedWebView.swift \
        Sources/Rendering/*.swift -o "$app/Contents/MacOS/$name"
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
<key>NSInputMonitoringUsageDescription</key><string>Route built-in keyboard input only while this research window has focus. No typed text or key codes enter saved logs.</string>
<key>NSAppTransportSecurity</key><dict><key>NSAllowsLocalNetworking</key><true/></dict>
</dict></plist>
EOF
    codesign --force --sign - --options runtime "$app"
    codesign --verify --strict "$app"
done

#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .build/module-cache dist
for variant in protected control; do
    if [ "$variant" = protected ]; then
        name=AgentFreeBrowser
        bundle=research.agentfreebrowser.protected
        defines=(-D PROTECTED_BUILD)
    else
        name=InspectableControl
        bundle=research.agentfreebrowser.control
        defines=(-D INSPECTION_CONTROL)
    fi
    app="dist/$name.app"
    mkdir -p "$app/Contents/MacOS"
    xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library -O -target arm64-apple-macosx14.0 \
        -module-cache-path .build/module-cache "${defines[@]}" \
        Sources/Browser/*.swift -o "$app/Contents/MacOS/$name"
    cat > "$app/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleIdentifier</key><string>$bundle</string>
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

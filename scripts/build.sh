#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .build/module-cache dist
variants=(protected control metadata secure reduced axboundary devicekeyboard)
if [ "$#" -gt 0 ]; then variants=("$@"); fi
for variant in "${variants[@]}"; do
    if [ "$variant" = protected ]; then
        name=AgentFreeBrowser
        bundle=research.agentfreebrowser.protected
        defines=(-D PROTECTED_BUILD)
    elif [ "$variant" = control ]; then
        name=InspectableControl
        bundle=research.agentfreebrowser.control
        defines=(-D INSPECTION_CONTROL)
    elif [ "$variant" = metadata ]; then
        name=MetadataExperiment
        bundle=research.agentfreebrowser.metadata
        defines=(-D METADATA_EXPERIMENT)
    elif [ "$variant" = secure ]; then
        name=SecureInputExperiment
        bundle=research.agentfreebrowser.secure
        defines=(-D SECURE_INPUT_EXPERIMENT)
    elif [ "$variant" = reduced ]; then
        name=ReducedExposureExperiment
        bundle=research.agentfreebrowser.reduced
        defines=(-D REDUCED_EXPOSURE_EXPERIMENT)
    elif [ "$variant" = axboundary ]; then
        name=AXBoundaryExperiment
        bundle=research.agentfreebrowser.axboundary
        defines=(-D AX_BOUNDARY_EXPERIMENT)
    elif [ "$variant" = devicekeyboard ]; then
        name=DeviceKeyboardExperiment
        bundle=research.agentfreebrowser.devicekeyboard
        defines=(-D DEVICE_KEYBOARD_EXPERIMENT)
    else
        echo "Unknown browser variant: $variant" >&2
        exit 2
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
<key>NSInputMonitoringUsageDescription</key><string>Route physical keyboard input only while this research window has focus. No typed text or key codes enter saved logs.</string>
<key>NSAppTransportSecurity</key><dict><key>NSAllowsLocalNetworking</key><true/></dict>
</dict></plist>
EOF
    if [ "$variant" = devicekeyboard ]; then
        codesign --force --sign - --options runtime "$app"
    else
        codesign --force --sign - --options runtime --entitlements config/browser.entitlements "$app"
    fi
    codesign --verify --strict "$app"
done

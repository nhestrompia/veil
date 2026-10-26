#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .build/module-cache
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library \
    -module-cache-path .build/module-cache \
    "$PWD/Sources/Diagnostics/WindowGeometryScope.swift" \
    "$PWD/Tests/WindowGeometryScopeTests.swift" -o .build/window-geometry-scope-tests
.build/window-geometry-scope-tests
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library \
    -module-cache-path .build/module-cache \
    "$PWD/Sources/Diagnostics/WindowGeometryScope.swift" \
    "$PWD/Sources/Diagnostics/RendererProcessScope.swift" \
    "$PWD/Sources/Probe/DesktopInputSafety.swift" \
    "$PWD/Sources/Diagnostics/ResearchWindowGeometry.swift" -o .build/research-window-geometry
codesign --force --sign - --options runtime .build/research-window-geometry
codesign --verify --strict .build/research-window-geometry
app=dist/WindowGeometryProbe.app
mkdir -p "$app/Contents/MacOS"
cp .build/research-window-geometry "$app/Contents/MacOS/WindowGeometryProbe"
cat > "$app/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleIdentifier</key><string>research.agentfreebrowser.windowgeometry</string>
<key>CFBundleName</key><string>WindowGeometryProbe</string>
<key>CFBundleExecutable</key><string>WindowGeometryProbe</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>LSUIElement</key><true/>
<key>LSMinimumSystemVersion</key><string>14.0</string>
</dict></plist>
EOF
codesign --force --sign - --options runtime "$app"
codesign --verify --strict "$app"
.build/research-window-geometry --preflight

#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
app=dist/WindowPolicyControl.app
mkdir -p .build/module-cache "$app/Contents/MacOS"
python3 - <<'PY'
from pathlib import Path
source = Path('Sources/Browser/BrowserApp.swift').read_text()
old = 'window = NSWindow(contentRect: frame, styleMask: style, backing: .buffered, defer: false)'
assert source.count(old) == 1
source = source.replace(old, 'window = FixedGeometryWindow(contentRect: frame, styleMask: style, backing: .buffered, defer: false)')
source = source.replace('let name = "Inspectable Control"', 'let name = "Window Policy Control"')
marker = 'window.makeKeyAndOrderFront(nil)'
assert source.count(marker) == 1
source = source.replace(marker, marker + '''
        if CommandLine.arguments.contains("--fixed-geometry") {
            (window as! FixedGeometryWindow).pinGeometry()
        }
        Task { @MainActor in
            try? await Task.sleep(for: .seconds(140))
            NSApp.terminate(nil)
        }
''', 1)
Path('.build/WindowPolicyControl.swift').write_text(source)
PY
sources=()
for source in Sources/Browser/*.swift; do
    if [ "$source" != Sources/Browser/BrowserApp.swift ]; then sources+=("$source"); fi
done
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library -O \
    -module-cache-path .build/module-cache -D INSPECTION_CONTROL \
    "${sources[@]}" Sources/Diagnostics/FixedGeometryWindow.swift \
    .build/WindowPolicyControl.swift -o "$app/Contents/MacOS/WindowPolicyControl"
cat > "$app/Contents/Info.plist" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleIdentifier</key><string>research.agentfreebrowser.windowpolicycontrol</string>
<key>CFBundleName</key><string>WindowPolicyControl</string>
<key>CFBundleExecutable</key><string>WindowPolicyControl</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>NSAppTransportSecurity</key><dict><key>NSAllowsLocalNetworking</key><true/></dict>
</dict></plist>
EOF
codesign --force --sign - --options runtime --entitlements config/browser.entitlements "$app"
codesign --verify --strict "$app"

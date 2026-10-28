#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
app=dist/LocalInspectorControl.app
mkdir -p .build/module-cache "$app/Contents/MacOS"
python3 - <<'PY'
from pathlib import Path
source = Path('Sources/Browser/BrowserApp.swift').read_text()
policy = '''        guard BrowserRuntimePolicy.disableDeveloperExtras() else {
            print("Browser startup refused: local developer tools remain enabled.")
            return
        }'''
assert source.count(policy) == 1
source = source.replace(policy, '        print("LOCAL_INSPECTOR_CONTROL startupPolicyOmitted=true")')
marker = '        window.title = name'
assert source.count(marker) == 1
source = source.replace(marker, '''        window.title = "Local inspector policy control"
        Task { @MainActor in
            try? await Task.sleep(for: .seconds(90))
            NSApp.terminate(nil)
        }''')
Path('.build/LocalInspectorControl.swift').write_text(source)
PY
sources=()
for source in Sources/Browser/*.swift; do
    if [ "$source" != Sources/Browser/BrowserApp.swift ]; then sources+=("$source"); fi
done
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library -O \
    -target arm64-apple-macosx14.0 -module-cache-path .build/module-cache \
    "${sources[@]}" .build/LocalInspectorControl.swift \
    -o "$app/Contents/MacOS/LocalInspectorControl"
cat > "$app/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<plist version="1.0"><dict>
<key>CFBundleIdentifier</key><string>research.agentfreebrowser.localinspectorcontrol</string>
<key>CFBundleName</key><string>LocalInspectorControl</string>
<key>CFBundleExecutable</key><string>LocalInspectorControl</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>NSAppTransportSecurity</key><dict><key>NSAllowsLocalNetworking</key><true/></dict>
</dict></plist>
EOF
codesign --force --sign - --options runtime --entitlements config/browser.entitlements "$app"
codesign --verify --strict "$app"

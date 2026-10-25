#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
app=dist/DeviceDispatchControl.app
mkdir -p .build/module-cache artifacts/address-dispatch "$app/Contents/MacOS"
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library -O \
    -D DEVICE_KEYBOARD_EXPERIMENT -target arm64-apple-macosx14.0 \
    -module-cache-path .build/module-cache Sources/Browser/AXBoundary.swift \
    Sources/Browser/DeviceKeyboard.swift Sources/Browser/HIDSourcePolicy.swift Sources/Diagnostics/AddressDispatchControl.swift -o "$app/Contents/MacOS/DeviceDispatchControl"
cat > "$app/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<plist version="1.0"><dict>
<key>CFBundleIdentifier</key><string>research.agentfreebrowser.devicedispatchcontrol</string>
<key>CFBundleName</key><string>DeviceDispatchControl</string>
<key>CFBundleExecutable</key><string>DeviceDispatchControl</string>
<key>CFBundlePackageType</key><string>APPL</string>
</dict></plist>
EOF
codesign --force --sign - --options runtime "$app"
for mode in direct queued startup; do
    open -n -W "$app" --args "$mode" "$PWD/artifacts/address-dispatch/$mode.json"
done
python3 - <<'PY'
import json
from pathlib import Path
for mode in ['direct', 'queued', 'startup']:
    result = json.loads(Path(f'artifacts/address-dispatch/{mode}.json').read_text())
    print(json.dumps(result))
    assert result['startupAddressPreserved'], f'{mode}: Space replaced the startup address'
    assert result['submittedActions'] == 1, f'{mode}: Return did not submit the address'
    assert result['normalSpaceWorks'], f'{mode}: Space failed after navigation began'
PY

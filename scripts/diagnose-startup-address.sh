#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
app=dist/AddressStartupControl.app
mkdir -p .build/module-cache "$app/Contents/MacOS"
python3 - <<'PY'
from pathlib import Path
source = Path('Sources/Browser/BrowserApp.swift').read_text()
marker = 'deviceKeyboard?.start()'
assert source.count(marker) == 1
source = source.replace(marker, '''
Task { @MainActor in
    try? await Task.sleep(for: .milliseconds(800))
    print("DEBUG_STARTUP focusEditor=\\(address.currentEditor() != nil) responder=\\(String(describing: type(of: window.firstResponder))) key=\\(window.isKeyWindow)")
    for down in [true, false] {
        let event = NSEvent.keyEvent(with: down ? .keyDown : .keyUp, location: .zero,
            modifierFlags: [], timestamp: ProcessInfo.processInfo.systemUptime,
            windowNumber: window.windowNumber, context: nil, characters: "\\r",
            charactersIgnoringModifiers: "\\r", isARepeat: false, keyCode: 36)!
        (NSApp as! DeviceKeyboardApplication).dispatchDeviceEvent(event)
    }
    try? await Task.sleep(for: .milliseconds(500))
    print("DEBUG_STARTUP navigated=\\(webView.url != nil)")
    fflush(stdout)
}
''')
marker = '@objc private func navigate() {'
assert source.count(marker) == 1
source = source.replace(marker, marker + '\n        print("DEBUG_STARTUP submitAction=true")\n        fflush(stdout)')
Path('.build/AddressStartupControl.swift').write_text(source)
PY
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library -O \
    -D DEVICE_KEYBOARD_EXPERIMENT -target arm64-apple-macosx14.0 -module-cache-path .build/module-cache \
    Sources/Browser/AXBoundary.swift Sources/Browser/DeviceKeyboard.swift Sources/Browser/BrowserPolicy.swift \
    Sources/Browser/BrowserRuntimePolicy.swift Sources/Browser/InputSourceWindow.swift \
    Sources/Browser/SecureInputWindow.swift .build/AddressStartupControl.swift \
    -o "$app/Contents/MacOS/AddressStartupControl"
cat > "$app/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<plist version="1.0"><dict>
<key>CFBundleIdentifier</key><string>research.agentfreebrowser.addressstartupcontrol</string>
<key>CFBundleName</key><string>AddressStartupControl</string>
<key>CFBundleExecutable</key><string>AddressStartupControl</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>NSAppTransportSecurity</key><dict><key>NSAllowsLocalNetworking</key><true/></dict>
</dict></plist>
EOF
codesign --force --sign - --options runtime "$app"
python3 tools/run_launch_navigation.py --targets InspectableControl AddressStartupControl --repetitions 1 --output artifacts/startup-dispatch-diagnosis

#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
app=dist/InternalKeyboardControl.app
restricted=false
build_only=false
for argument in "$@"; do
    case "$argument" in
        --capture-restricted) restricted=true ;;
        --build-only) build_only=true ;;
        *) echo "Unknown diagnostic option: $argument" >&2; exit 2 ;;
    esac
done
defines=(-D DEVICE_KEYBOARD_EXPERIMENT)
if [ "$restricted" = false ]; then defines+=(-D DEVICE_VISIBLE_CONTROL); fi
mkdir -p .build/module-cache "$app/Contents/MacOS"
python3 - <<'PY'
from pathlib import Path
source = Path('Sources/Browser/BrowserApp.swift').read_text()
marker = 'deviceKeyboard?.start()'
assert source.count(marker) == 1
source = source.replace(marker, '''
window.title = "Internal keyboard functionality control"
print("INTERNAL_KEYBOARD windowSharingEnabled=\\(window.sharingType != .none)")
Task { @MainActor in
    try? await Task.sleep(for: .milliseconds(700))
    let app = NSApp as! DeviceKeyboardApplication
    @MainActor func key(_ code: UInt16, _ text: String, _ flags: NSEvent.ModifierFlags = []) {
        for down in [true, false] {
            let event = NSEvent.keyEvent(with: down ? .keyDown : .keyUp, location: .zero,
                modifierFlags: flags, timestamp: ProcessInfo.processInfo.systemUptime,
                windowNumber: window.windowNumber, context: nil, characters: text,
                charactersIgnoringModifiers: text, isARepeat: false, keyCode: code)!
            app.dispatchDeviceEvent(event)
        }
    }
    key(49, " ")
    key(49, " ")
    print("INTERNAL_KEYBOARD startupAddressPreserved=\\(address.stringValue == CommandLine.arguments.last)")
    key(36, "\\r")
    try? await Task.sleep(for: .milliseconds(500))
    for _ in 0..<30 {
        if !webView.isLoading { break }
        try? await Task.sleep(for: .milliseconds(100))
    }
    key(37, "l", .command)
    print("INTERNAL_KEYBOARD locationHasEditor=\\(address.currentEditor() != nil)")
    key(36, "\\r")
    try? await Task.sleep(for: .milliseconds(500))
    for _ in 0..<30 {
        if !webView.isLoading { break }
        try? await Task.sleep(for: .milliseconds(100))
    }
    key(48, "\\t")
    let codes: [UInt16] = [45, 0, 17, 34, 9, 14, 27, 34, 45, 35, 32, 17, 36]
    for (code, character) in zip(codes, "native-input\\r") {
        key(code, String(character))
        try? await Task.sleep(for: .milliseconds(50))
    }
    print("INTERNAL_KEYBOARD sequenceFinished=true noDeviceReader=true")
    fflush(stdout)
}
''')
Path('.build/InternalKeyboardControl.swift').write_text(source)
PY
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library -O \
    "${defines[@]}" -target arm64-apple-macosx14.0 \
    -module-cache-path .build/module-cache Sources/Browser/AXBoundary.swift \
    Sources/Browser/DeviceKeyboard.swift Sources/Browser/BrowserPolicy.swift \
    Sources/Browser/InputSourceWindow.swift Sources/Browser/SecureInputWindow.swift \
    .build/InternalKeyboardControl.swift -o "$app/Contents/MacOS/InternalKeyboardControl"
cat > "$app/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<plist version="1.0"><dict>
<key>CFBundleIdentifier</key><string>research.agentfreebrowser.internalkeyboardcontrol</string>
<key>CFBundleName</key><string>InternalKeyboardControl</string>
<key>CFBundleExecutable</key><string>InternalKeyboardControl</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>NSAppTransportSecurity</key><dict><key>NSAllowsLocalNetworking</key><true/></dict>
</dict></plist>
EOF
codesign --force --sign - --options runtime "$app"
if [ "$build_only" = false ]; then python3 tools/run_internal_keyboard_control.py; fi

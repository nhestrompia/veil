#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
app=dist/InternalKeyboardControl.app
restricted=false
build_only=false
backdrop=false
invalid_backdrop=false
feature_suite=false
focus_mode=ordinary
focus_resume=false
for argument in "$@"; do
    case "$argument" in
        --capture-restricted) restricted=true ;;
        --build-only) build_only=true ;;
        --backdrop) backdrop=true ;;
        --invalid-backdrop) backdrop=true; invalid_backdrop=true ;;
        --feature-suite) feature_suite=true ;;
        --filter-activation) focus_mode=filter ;;
        --logical-key) focus_mode=logical ;;
        --stable-activity) focus_mode=stable ;;
        --focus-resume) focus_resume=true ;;
        *) echo "Unknown diagnostic option: $argument" >&2; exit 2 ;;
    esac
done
defines=(-D DEVICE_KEYBOARD_EXPERIMENT)
if [ "$restricted" = false ]; then defines+=(-D DEVICE_VISIBLE_CONTROL); fi
if [ "$backdrop" = true ]; then defines+=(-D INTERNAL_CAPTURE_BACKDROP); fi
if [ "$invalid_backdrop" = true ]; then defines+=(-D INTERNAL_SMALL_CAPTURE_BACKDROP); fi
if [ "$feature_suite" = true ]; then defines+=(-D INTERNAL_FEATURE_SUITE); fi
if [ "$focus_resume" = true ]; then defines+=(-D INTERNAL_FOCUS_RESUME); fi
case "$focus_mode" in
    filter) defines+=(-D INTERNAL_ACTIVATION_FILTER) ;;
    logical) defines+=(-D INTERNAL_LOGICAL_KEY) ;;
    stable) defines+=(-D INTERNAL_STABLE_ACTIVITY) ;;
esac
mkdir -p .build/module-cache "$app/Contents/MacOS"
python3 - <<'PY'
from pathlib import Path
boundary = Path('Sources/Browser/AXBoundary.swift').read_text()
assert boundary.count('final class AXBoundaryWindow: NSWindow {') == 1
boundary = boundary.replace('import AppKit', 'import AppKit\nimport Carbon', 1)
boundary = boundary.replace('final class AXBoundaryWindow: NSWindow {', '''final class AXBoundaryWindow: NSWindow {
    #if INTERNAL_LOGICAL_KEY || INTERNAL_STABLE_ACTIVITY
    override var isKeyWindow: Bool { true }
    #endif
    #if INTERNAL_STABLE_ACTIVITY
    override var isVisible: Bool { true }
    override var occlusionState: NSWindow.OcclusionState { .visible }
    #endif

    var diagnosticActualKeyWindow: Bool { super.isKeyWindow }

    override func becomeKey() {
        super.becomeKey()
        reportDiagnosticFocus("became-key")
    }

    override func resignKey() {
        super.resignKey()
        reportDiagnosticFocus("resigned-key")
    }

    private func reportDiagnosticFocus(_ phase: String) {
        print("FOCUS_DIAGNOSTIC phase=\\(phase) actualKey=\\(super.isKeyWindow) logicalKey=\\(isKeyWindow) actualVisible=\\(super.isVisible) logicalVisible=\\(isVisible) foreground=\\(NSWorkspace.shared.frontmostApplication?.processIdentifier ?? -1) secureInput=\\(IsSecureEventInputEnabled())")
        fflush(stdout)
    }
''', 1)
Path('.build/InternalFocusBoundary.swift').write_text(boundary)
device = Path('Sources/Browser/DeviceKeyboard.swift').read_text()
assert device.count('guard let window, window.isKeyWindow,') == 1
device = device.replace('guard let window, window.isKeyWindow,',
                        'guard let window, (window as? AXBoundaryWindow)?.diagnosticActualKeyWindow == true,', 1)
device = device.replace('''        switch event.type {''', '''        #if INTERNAL_ACTIVATION_FILTER
        if event.type == .appKitDefined,
           event.subtype == .applicationActivated || event.subtype == .applicationDeactivated {
            print("FOCUS_ACTIVATION_REFUSED subtype=\\(event.subtype.rawValue)")
            fflush(stdout)
            return
        }
        #endif
        switch event.type {''', 1)
Path('.build/InternalFocusDeviceKeyboard.swift').write_text(device)
source = Path('Sources/Browser/BrowserApp.swift').read_text()
marker = 'deviceKeyboard?.start()'
assert source.count(marker) == 1
source = source.replace('private var window: NSWindow!', 'private var window: NSWindow!\n    private var diagnosticBackdrop: NSWindow?')
source = source.replace(marker, '''
window.title = "Internal keyboard functionality control"
Task { @MainActor in
    try? await Task.sleep(for: .seconds(90))
    print("INTERNAL_KEYBOARD watchdog=true")
    fflush(stdout)
    NSApp.terminate(nil)
}
print("INTERNAL_KEYBOARD windowSharingEnabled=\\(window.sharingType != .none)")
#if INTERNAL_CAPTURE_BACKDROP
if let screen = window.screen {
    #if INTERNAL_SMALL_CAPTURE_BACKDROP
    let backdropFrame = NSRect(x: 0, y: 0, width: 40, height: 40)
    #else
    let backdropFrame = screen.frame
    #endif
    let backdrop = NSWindow(contentRect: backdropFrame, styleMask: .borderless, backing: .buffered, defer: false)
    backdrop.title = "Controlled research backdrop"
    backdrop.isOpaque = true
    backdrop.alphaValue = 1
    backdrop.backgroundColor = NSColor(calibratedRed: 0.02, green: 0.62, blue: 0.65, alpha: 1)
    backdrop.hasShadow = false
    backdrop.ignoresMouseEvents = true
    backdrop.level = .screenSaver
    let label = NSTextField(labelWithString: "Controlled research backdrop")
    label.font = .systemFont(ofSize: 32)
    label.textColor = .white
    label.frame = NSRect(x: 260, y: screen.frame.height / 2, width: 720, height: 50)
    backdrop.contentView?.addSubview(label)
    diagnosticBackdrop = backdrop
    window.level = NSWindow.Level(rawValue: NSWindow.Level.screenSaver.rawValue + 1)
    backdrop.orderFrontRegardless()
    window.makeKeyAndOrderFront(nil)
    NSApp.activate(ignoringOtherApps: true)
    print("INTERNAL_CAPTURE targetWindow=\\(window.windowNumber) backdropWindow=\\(backdrop.windowNumber)")
}
#endif
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
    print("INTERNAL_KEYBOARD locationUsesRestrictedEditor=\\(address.currentEditor() is DeviceFieldEditor)")
    key(36, "\\r")
    try? await Task.sleep(for: .milliseconds(500))
    for _ in 0..<30 {
        if !webView.isLoading { break }
        try? await Task.sleep(for: .milliseconds(100))
    }
    #if INTERNAL_FEATURE_SUITE
    _ = try? await webView.evaluateJavaScript("window.focusResearchField()")
    try? await Task.sleep(for: .milliseconds(300))
    print("INTERNAL_KEYBOARD focusAssistedByDiagnostic=true")
    #else
    key(48, "\\t")
    #endif
    let codes: [UInt16] = [45, 0, 17, 34, 9, 14, 27, 34, 45, 35, 32, 17, 36]
    let automaticSubmit = URLComponents(string: CommandLine.arguments.last ?? "")?.queryItems?.contains {
        $0.name == "submit-on-input" && $0.value == "1"
    } == true
    let text = automaticSubmit ? "native-input" : "native-input\\r"
    for (code, character) in zip(codes, text) {
        key(code, String(character))
        try? await Task.sleep(for: .milliseconds(50))
    }
    print("INTERNAL_KEYBOARD inputTriggeredSubmit=\\(automaticSubmit)")
    print("INTERNAL_KEYBOARD sequenceFinished=true noDeviceReader=true")
    fflush(stdout)
    #if INTERNAL_FOCUS_RESUME
    try? await Task.sleep(for: .seconds(8))
    for (code, character) in zip(codes, "native-input\\r") {
        key(code, String(character))
        try? await Task.sleep(for: .milliseconds(50))
    }
    print("INTERNAL_KEYBOARD resumeSequenceFinished=true")
    fflush(stdout)
    #endif
}
''')
Path('.build/InternalKeyboardControl.swift').write_text(source)
PY
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library -O \
    "${defines[@]}" -target arm64-apple-macosx14.0 \
    -module-cache-path .build/module-cache .build/InternalFocusBoundary.swift \
    .build/InternalFocusDeviceKeyboard.swift Sources/Browser/HIDSourcePolicy.swift Sources/Browser/BrowserPolicy.swift \
    Sources/Browser/RestrictedWebView.swift \
    Sources/Browser/BrowserRuntimePolicy.swift \
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

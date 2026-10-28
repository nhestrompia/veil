import AppKit

@MainActor
final class AddressDispatchControl: NSObject, NSApplicationDelegate {
    let mode: String
    let output: URL
    private var window: NSWindow!
    private let field = NSTextField()
    private var actions = 0

    init(mode: String, output: URL) { self.mode = mode; self.output = output }

    func applicationDidFinishLaunching(_ notification: Notification) {
        window = NSWindow(contentRect: NSRect(x: 100, y: 100, width: 700, height: 300),
                          styleMask: [.titled, .closable], backing: .buffered, defer: false)
        window.title = "Native address dispatch control"
        field.frame = NSRect(x: 20, y: 160, width: 600, height: 30)
        field.stringValue = "native-input"
        field.target = self
        field.action = #selector(submitted)
        window.contentView?.addSubview(field)
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        let focused = window.makeFirstResponder(field)
        Task { @MainActor in
            try? await Task.sleep(for: .milliseconds(400))
            let hasEditor = field.currentEditor() != nil
            if mode == "startup" {
                for _ in 0..<3 {
                    for down in [true, false] {
                        let event = NSEvent.keyEvent(with: down ? .keyDown : .keyUp, location: .zero,
                            modifierFlags: [], timestamp: ProcessInfo.processInfo.systemUptime,
                            windowNumber: window.windowNumber, context: nil, characters: " ",
                            charactersIgnoringModifiers: " ", isARepeat: false, keyCode: 49)!
                        (NSApp as! DeviceKeyboardApplication).dispatchDeviceEvent(event)
                    }
                }
            }
            let startupAddressPreserved = field.stringValue == "native-input"
            for down in [true, false] {
                let event = NSEvent.keyEvent(with: down ? .keyDown : .keyUp, location: .zero,
                    modifierFlags: [], timestamp: ProcessInfo.processInfo.systemUptime,
                    windowNumber: window.windowNumber, context: nil, characters: "\r",
                    charactersIgnoringModifiers: "\r", isARepeat: false, keyCode: 36)!
                if let app = NSApp as? DeviceKeyboardApplication { app.dispatchDeviceEvent(event) }
                else { NSApp.postEvent(event, atStart: false) }
            }
            try? await Task.sleep(for: .milliseconds(300))
            var normalSpaceWorks = true
            if mode == "startup", let app = NSApp as? DeviceKeyboardApplication {
                app.didBeginNavigation()
                window.makeFirstResponder(field)
                field.selectText(nil)
                for down in [true, false] {
                    let event = NSEvent.keyEvent(with: down ? .keyDown : .keyUp, location: .zero,
                        modifierFlags: [], timestamp: ProcessInfo.processInfo.systemUptime,
                        windowNumber: window.windowNumber, context: nil, characters: " ",
                        charactersIgnoringModifiers: " ", isARepeat: false, keyCode: 49)!
                    app.dispatchDeviceEvent(event)
                }
                normalSpaceWorks = field.stringValue == " "
            }
            let result: [String: Any] = ["mode": mode, "focusRequest": focused, "hasEditor": hasEditor,
                "windowIsKey": window.isKeyWindow, "submittedActions": actions, "noDeviceReader": true,
                "startupAddressPreserved": startupAddressPreserved, "normalSpaceWorks": normalSpaceWorks]
            try? JSONSerialization.data(withJSONObject: result, options: [.prettyPrinted, .sortedKeys]).write(to: output)
            NSApp.terminate(nil)
        }
    }

    @objc private func submitted() { actions += 1 }
}

@main
enum DeviceAddressDispatchTests {
    @MainActor static func main() {
        let args = CommandLine.arguments
        guard args.count == 3, ["direct", "queued", "startup"].contains(args[1]), args[2].hasPrefix("/") else { exit(2) }
        let app = args[1] == "queued" ? NSApplication.shared : DeviceKeyboardApplication.shared
        let delegate = AddressDispatchControl(mode: args[1], output: URL(fileURLWithPath: args[2]))
        app.setActivationPolicy(.regular)
        app.delegate = delegate
        withExtendedLifetime(delegate) { app.run() }
    }
}

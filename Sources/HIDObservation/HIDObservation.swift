import AppKit
import IOKit.hid
import IOKit.hidsystem

@MainActor
final class HIDObserver: NSObject, NSApplicationDelegate {
    private var window: NSWindow!
    private let status = NSTextField(labelWithString: "Observation is stopped. No input defense is active.")
    private let field = NSTextField()
    private let manager = IOHIDManagerCreate(kCFAllocatorDefault, IOOptionBits(kIOHIDOptionsTypeNone))
    private var monitor: Any?
    private var records: [[String: Any]] = []
    private var devices: [IOHIDDevice: Int] = [:]
    private var collecting = false
    private var managerOpen = false
    private var submitted = 0
    private var output: URL?
    private var stopTask: Task<Void, Never>?
    private var timebase = mach_timebase_info_data_t()

    func applicationDidFinishLaunching(_ notification: Notification) {
        let args = CommandLine.arguments
        mach_timebase_info(&timebase)
        if let index = args.firstIndex(of: "--out"), args.indices.contains(index + 1), args[index + 1].hasPrefix("/") {
            output = URL(fileURLWithPath: args[index + 1])
        }
        field.placeholderString = "Use only the fake value native-input"
        field.setAccessibilityLabel("Enter native-input")
        field.target = self
        field.action = #selector(recordAction)
        let action = NSButton(title: "Record action", target: self, action: #selector(recordAction))
        let start = NSButton(title: "Start observation", target: self, action: #selector(startObservation))
        let stop = NSButton(title: "Stop and save", target: self, action: #selector(stopObservation))
        let explanation = NSTextField(wrappingLabelWithString:
            "This experiment compares raw device values with app events while this window has focus. It saves timing, pointer data, and event categories. It omits typed text, key codes, and device names. A computer-use tool is a synthetic control, not a human baseline.")
        let stack = NSStackView(views: [explanation, field, action, start, stop, status])
        stack.orientation = .vertical
        stack.alignment = .leading
        stack.spacing = 16
        let content = NSView()
        content.addSubview(stack)
        stack.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            stack.leadingAnchor.constraint(equalTo: content.leadingAnchor, constant: 24),
            stack.trailingAnchor.constraint(equalTo: content.trailingAnchor, constant: -24),
            stack.topAnchor.constraint(equalTo: content.topAnchor, constant: 24),
            field.widthAnchor.constraint(equalToConstant: 500),
        ])
        window = NSWindow(contentRect: NSRect(x: 100, y: 100, width: 700, height: 400),
            styleMask: [.titled, .closable, .miniaturizable], backing: .buffered, defer: false)
        window.title = "Raw HID Observation"
        window.contentView = content
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        monitor = NSEvent.addLocalMonitorForEvents(matching: [.mouseMoved, .leftMouseDown, .leftMouseUp,
            .leftMouseDragged, .rightMouseDown, .rightMouseUp, .scrollWheel, .keyDown, .keyUp]) { [weak self] event in
            MainActor.assumeIsolated {
                if let self, self.collecting, self.window.isKeyWindow,
                   NSWorkspace.shared.frontmostApplication?.processIdentifier == getpid(), self.records.count < 10000 {
                    var entry: [String: Any] = ["origin": "app-event", "type": event.type.rawValue,
                        "timestampSeconds": event.timestamp,
                        "sourceState": event.cgEvent?.getIntegerValueField(.eventSourceStateID) ?? -999]
                    if event.type != .keyDown && event.type != .keyUp {
                        entry["point"] = [event.locationInWindow.x, event.locationInWindow.y]
                    }
                    self.records.append(entry)
                }
            }
            return event
        }
        window.acceptsMouseMovedEvents = true
        if args.contains("--observe") { startObservation() }
        save()
    }

    @objc private func startObservation() {
        guard !collecting else { return }
        guard IOHIDCheckAccess(kIOHIDRequestTypeListenEvent) == kIOHIDAccessTypeGranted else {
            status.stringValue = "Input Monitoring is absent. No permission request occurs from this button."
            return
        }
        if !managerOpen {
            let matching: [[String: Int]] = [kHIDUsage_GD_Keyboard, kHIDUsage_GD_Mouse, kHIDUsage_GD_Pointer].map {
                [kIOHIDDeviceUsagePageKey: kHIDPage_GenericDesktop, kIOHIDDeviceUsageKey: $0]
            }
            IOHIDManagerSetDeviceMatchingMultiple(manager, matching as CFArray)
            IOHIDManagerRegisterInputValueCallback(manager, { context, result, _, value in
                guard result == kIOReturnSuccess, let context else { return }
                // The manager delivers this callback on the scheduled main run loop.
                MainActor.assumeIsolated {
                    Unmanaged<HIDObserver>.fromOpaque(context).takeUnretainedValue().receive(value)
                }
            }, Unmanaged.passUnretained(self).toOpaque())
            IOHIDManagerScheduleWithRunLoop(manager, CFRunLoopGetMain(), CFRunLoopMode.commonModes.rawValue)
            let result = IOHIDManagerOpen(manager, IOOptionBits(kIOHIDOptionsTypeNone))
            guard result == kIOReturnSuccess else {
                IOHIDManagerUnscheduleFromRunLoop(manager, CFRunLoopGetMain(), CFRunLoopMode.commonModes.rawValue)
                status.stringValue = "Raw device access failed. Status \(result). No prevention result."
                return
            }
            managerOpen = true
        }
        records = []
        devices = [:]
        collecting = true
        status.stringValue = "Observation active only while this window has focus. Use fake text only."
        if let index = CommandLine.arguments.firstIndex(of: "--duration"),
           CommandLine.arguments.indices.contains(index + 1), let seconds = Int(CommandLine.arguments[index + 1]),
           (1...120).contains(seconds) {
            stopTask?.cancel()
            stopTask = Task { [weak self] in
                do { try await Task.sleep(for: .seconds(seconds)) } catch { return }
                self?.stopObservation()
            }
        }
    }

    private func receive(_ value: IOHIDValue) {
        guard collecting, window.isKeyWindow, NSWorkspace.shared.frontmostApplication?.processIdentifier == getpid(),
              records.count < 10000 else { return }
        let element = IOHIDValueGetElement(value)
        let page = IOHIDElementGetUsagePage(element)
        let usage = IOHIDElementGetUsage(element)
        let category: String
        switch (page, usage) {
        case (UInt32(kHIDPage_KeyboardOrKeypad), _): category = "keyboard"
        case (UInt32(kHIDPage_Button), _): category = "button"
        case (UInt32(kHIDPage_GenericDesktop), UInt32(kHIDUsage_GD_X)): category = "x"
        case (UInt32(kHIDPage_GenericDesktop), UInt32(kHIDUsage_GD_Y)): category = "y"
        case (UInt32(kHIDPage_GenericDesktop), UInt32(kHIDUsage_GD_Wheel)): category = "wheel"
        default: return
        }
        let device = IOHIDElementGetDevice(element)
        if devices[device] == nil { devices[device] = devices.count + 1 }
        var entry: [String: Any] = ["origin": "device-value", "category": category,
            "timestampTicks": IOHIDValueGetTimeStamp(value),
            "timestampSeconds": Double(IOHIDValueGetTimeStamp(value)) * Double(timebase.numer) / Double(timebase.denom) / 1_000_000_000,
            "deviceOrdinal": devices[device] ?? 0]
        // Keyboard usage and values can reconstruct text, so neither enters the saved record.
        if category != "keyboard" { entry["value"] = IOHIDValueGetIntegerValue(value) }
        records.append(entry)
    }

    @objc private func recordAction() {
        if field.stringValue == "native-input" { submitted += 1 }
        save()
    }

    @objc private func stopObservation() {
        stopTask?.cancel()
        collecting = false
        save()
        status.stringValue = "Observation stopped. Saved \(records.count) events. No human baseline is certified."
    }

    private func save() {
        guard let output else {
            status.stringValue = "No output path. Launch with --out and an absolute JSON path."
            return
        }
        let value: [String: Any] = ["records": records, "acceptedFakeActions": submitted,
            "pid": getpid(), "collecting": collecting,
            "humanBaselineVerified": false, "isInputDefense": false,
            "recordLimitReached": records.count >= 10000,
            "inputMonitoringAccess": IOHIDCheckAccess(kIOHIDRequestTypeListenEvent).rawValue]
        do {
            try JSONSerialization.data(withJSONObject: value, options: [.prettyPrinted, .sortedKeys]).write(to: output, options: .atomic)
        } catch { status.stringValue = "Save failed. \(error.localizedDescription)" }
    }

    func applicationWillResignActive(_ notification: Notification) { if collecting { save() } }
    func applicationWillTerminate(_ notification: Notification) {
        stopTask?.cancel()
        collecting = false
        if managerOpen {
            IOHIDManagerUnscheduleFromRunLoop(manager, CFRunLoopGetMain(), CFRunLoopMode.commonModes.rawValue)
            IOHIDManagerClose(manager, IOOptionBits(kIOHIDOptionsTypeNone))
        }
        if let monitor { NSEvent.removeMonitor(monitor) }
        save()
    }
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }
}

@main
enum ObservationApp {
    @MainActor static func main() {
        let app = NSApplication.shared
        if CommandLine.arguments.contains("--permissions") || CommandLine.arguments.contains("--request-permissions") {
            if CommandLine.arguments.contains("--request-permissions") {
                _ = IOHIDRequestAccess(kIOHIDRequestTypeListenEvent)
            }
            let value: [String: Any] = ["inputMonitoringAccess": IOHIDCheckAccess(kIOHIDRequestTypeListenEvent).rawValue,
                "inputMonitoringGranted": IOHIDCheckAccess(kIOHIDRequestTypeListenEvent) == kIOHIDAccessTypeGranted]
            do {
                let data = try JSONSerialization.data(withJSONObject: value, options: [.prettyPrinted, .sortedKeys])
                let args = CommandLine.arguments
                if let index = args.firstIndex(of: "--out"), args.indices.contains(index + 1), args[index + 1].hasPrefix("/") {
                    try data.write(to: URL(fileURLWithPath: args[index + 1]), options: .atomic)
                }
                print(String(decoding: data, as: UTF8.self))
            } catch { print("Permission-result write failed. \(error.localizedDescription)"); exit(2) }
            return
        }
        let observer = HIDObserver()
        app.setActivationPolicy(.regular)
        app.delegate = observer
        withExtendedLifetime(observer) { app.run() }
    }
}

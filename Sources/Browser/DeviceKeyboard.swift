import AppKit
import IOKit.hid
import IOKit.hidsystem

#if DEVICE_KEYBOARD_EXPERIMENT
@MainActor
enum DeviceDragGate {
    static func refuseOperation(_ phase: String) -> NSDragOperation {
        print("DRAG_GATE_REFUSED phase=\(phase)")
        fflush(stdout)
        return []
    }

    static func refuseImport(_ phase: String) -> Bool {
        print("DRAG_GATE_REFUSED phase=\(phase)")
        fflush(stdout)
        return false
    }
}

@MainActor
final class DeviceAddressField: NSTextField {
    override func draggingEntered(_ sender: any NSDraggingInfo) -> NSDragOperation { DeviceDragGate.refuseOperation("address.entered") }
    override func draggingUpdated(_ sender: any NSDraggingInfo) -> NSDragOperation { DeviceDragGate.refuseOperation("address.updated") }
    override func prepareForDragOperation(_ sender: any NSDraggingInfo) -> Bool { DeviceDragGate.refuseImport("address.prepare") }
    override func performDragOperation(_ sender: any NSDraggingInfo) -> Bool { DeviceDragGate.refuseImport("address.perform") }
}

@MainActor
final class DeviceFieldEditor: NSTextView {
    override func draggingEntered(_ sender: any NSDraggingInfo) -> NSDragOperation { DeviceDragGate.refuseOperation("editor.entered") }
    override func draggingUpdated(_ sender: any NSDraggingInfo) -> NSDragOperation { DeviceDragGate.refuseOperation("editor.updated") }
    override func prepareForDragOperation(_ sender: any NSDraggingInfo) -> Bool { DeviceDragGate.refuseImport("editor.prepare") }
    override func performDragOperation(_ sender: any NSDraggingInfo) -> Bool { DeviceDragGate.refuseImport("editor.perform") }
}

@MainActor
final class DeviceEventGate {
    private var pending: [ObjectIdentifier: NSEvent] = [:]

    func authorize(_ event: NSEvent) { pending[ObjectIdentifier(event)] = event }
    func consume(_ event: NSEvent) -> Bool {
        pending.removeValue(forKey: ObjectIdentifier(event)) != nil
    }
    func clear() { pending.removeAll() }
}

@MainActor
final class DeviceKeyboardApplication: AXBoundaryApplication {
    let deviceGate = DeviceEventGate()
    private(set) var acceptedEventCount = 0
    private(set) var refusedEventCount = 0
    private var awaitingInitialNavigation = true
    var onOpenLocation: (() -> Void)?

    func didBeginNavigation() { awaitingInitialNavigation = false }

    func dispatchDeviceEvent(_ event: NSEvent) {
        // Repeated binding gestures must not replace the selected startup URL.
        if awaitingInitialNavigation, event.keyCode == 49 { return }
        deviceGate.authorize(event)
        sendEvent(event)
    }

    override func sendEvent(_ event: NSEvent) {
        switch event.type {
        case .appKitDefined, .systemDefined, .applicationDefined, .periodic:
            super.sendEvent(event)
        default:
            guard deviceGate.consume(event) else {
                refusedEventCount += 1
                print("INPUT_GATE_REFUSED type=\(event.type.rawValue)")
                fflush(stdout)
                return
            }
            acceptedEventCount += 1
            print("INPUT_GATE_ACCEPTED type=\(event.type.rawValue)")
            fflush(stdout)
            if event.type == .keyDown, event.keyCode == 37, event.modifierFlags.contains(.command),
               let onOpenLocation {
                onOpenLocation()
                return
            }
            super.sendEvent(event)
        }
    }
}

@MainActor
final class DeviceKeyboardRouter {
    private let manager = IOHIDManagerCreate(kCFAllocatorDefault, IOOptionBits(kIOHIDOptionsTypeNone))
    private weak var window: NSWindow?
    private var boundDevice: IOHIDDevice?
    private var pressed: Set<UInt32> = []
    private var opened = false
    private var reportedSourceRefusals: Set<String> = []
    private let onBind: () -> Void

    init(window: NSWindow, onBind: @escaping () -> Void) {
        self.window = window
        self.onBind = onBind
    }

    func start() {
        guard !opened else { return }
        guard IOHIDCheckAccess(kIOHIDRequestTypeListenEvent) == kIOHIDAccessTypeGranted else {
            print("DEVICE_KEYBOARD permission=false; no automatic request")
            fflush(stdout)
            return
        }
        IOHIDManagerSetDeviceMatching(manager, [kIOHIDDeviceUsagePageKey: kHIDPage_GenericDesktop,
            kIOHIDDeviceUsageKey: kHIDUsage_GD_Keyboard] as CFDictionary)
        IOHIDManagerRegisterInputValueCallback(manager, { context, result, _, value in
            guard result == kIOReturnSuccess, let context else { return }
            MainActor.assumeIsolated {
                Unmanaged<DeviceKeyboardRouter>.fromOpaque(context).takeUnretainedValue().receive(value)
            }
        }, Unmanaged.passUnretained(self).toOpaque())
        IOHIDManagerRegisterDeviceRemovalCallback(manager, { context, _, _, device in
            guard let context else { return }
            MainActor.assumeIsolated {
                let router = Unmanaged<DeviceKeyboardRouter>.fromOpaque(context).takeUnretainedValue()
                if router.boundDevice == device {
                    router.boundDevice = nil
                    router.resetPending()
                    print("DEVICE_KEYBOARD bindingRemoved=true")
                    fflush(stdout)
                }
            }
        }, Unmanaged.passUnretained(self).toOpaque())
        IOHIDManagerScheduleWithRunLoop(manager, CFRunLoopGetMain(), CFRunLoopMode.commonModes.rawValue)
        let result = IOHIDManagerOpen(manager, IOOptionBits(kIOHIDOptionsTypeNone))
        opened = result == kIOReturnSuccess
        if !opened { IOHIDManagerUnscheduleFromRunLoop(manager, CFRunLoopGetMain(), CFRunLoopMode.commonModes.rawValue) }
        print("DEVICE_KEYBOARD permission=true openStatus=\(result) bindWithDeviceSpace=true sourcePolicy=measured-built-in-keyboard")
        fflush(stdout)
    }

    func resetPending() {
        pressed.removeAll()
        (NSApp as? DeviceKeyboardApplication)?.deviceGate.clear()
    }

    func stop() {
        resetPending()
        boundDevice = nil
        if opened {
            IOHIDManagerUnscheduleFromRunLoop(manager, CFRunLoopGetMain(), CFRunLoopMode.commonModes.rawValue)
            IOHIDManagerClose(manager, IOOptionBits(kIOHIDOptionsTypeNone))
            opened = false
        }
    }

    private func receive(_ value: IOHIDValue) {
        guard let window, window.isKeyWindow,
              NSWorkspace.shared.frontmostApplication?.processIdentifier == getpid() else { return }
        let element = IOHIDValueGetElement(value)
        guard IOHIDElementGetUsagePage(element) == kHIDPage_KeyboardOrKeypad else { return }
        let usage = IOHIDElementGetUsage(element)
        let down = IOHIDValueGetIntegerValue(value) != 0
        let device = IOHIDElementGetDevice(element)
        if boundDevice == nil {
            // Binding is a research bootstrap, not authenticated human consent.
            if usage == 44, down {
                let source = HIDSourceSnapshot.observe(IOHIDDeviceGetService(device))
                let decision = HIDSourcePolicy.evaluate(source)
                guard decision == .measuredBuiltInKeyboard else {
                    if reportedSourceRefusals.insert(decision.rawValue).inserted {
                        print("DEVICE_KEYBOARD sourceRefused=\(decision.rawValue)")
                        fflush(stdout)
                    }
                    return
                }
                boundDevice = device
                pressed = [44]
                print("DEVICE_KEYBOARD bound=true bootstrapAttested=false")
                fflush(stdout)
                onBind()
            }
            return
        }
        guard device == boundDevice else { return }
        let wasDown = pressed.contains(usage)
        guard down != wasDown else { return }
        if down { pressed.insert(usage) } else { pressed.remove(usage) }
        if (224...231).contains(usage) { return }
        guard let key = Self.keys[usage], let app = NSApp as? DeviceKeyboardApplication else { return }
        var flags: NSEvent.ModifierFlags = []
        for (left, right, flag): (UInt32, UInt32, NSEvent.ModifierFlags) in [
            (224, 228, .control), (225, 229, .shift), (226, 230, .option), (227, 231, .command)
        ] {
            if pressed.contains(left) || pressed.contains(right) { flags.insert(flag) }
        }
        let character = flags.contains(.shift) ? key.shifted : key.plain
        guard let event = NSEvent.keyEvent(with: down ? .keyDown : .keyUp, location: .zero,
            modifierFlags: flags, timestamp: ProcessInfo.processInfo.systemUptime,
            windowNumber: window.windowNumber, context: nil, characters: character,
            charactersIgnoringModifiers: key.plain, isARepeat: false, keyCode: key.code) else { return }
        app.dispatchDeviceEvent(event)
    }

    private struct Key {
        let code: UInt16
        let plain: String
        let shifted: String
    }

    // This first routing experiment supports US ASCII and navigation keys only.
    private static let keys: [UInt32: Key] = {
        let letters: [UInt16] = [0,11,8,2,14,3,5,4,34,38,40,37,46,45,31,35,12,15,1,17,32,9,13,7,16,6]
        var keys: [UInt32: Key] = [:]
        for (index, code) in letters.enumerated() {
            let character = String(UnicodeScalar(97 + index)!)
            keys[UInt32(index + 4)] = Key(code: code, plain: character, shifted: character.uppercased())
        }
        let punctuation: [(UInt32, UInt16, String, String)] = [
            (30,18,"1","!"),(31,19,"2","@"),(32,20,"3","#"),(33,21,"4","$"),
            (34,23,"5","%"),(35,22,"6","^"),(36,26,"7","&"),(37,28,"8","*"),
            (38,25,"9","("),(39,29,"0",")"),(40,36,"\r","\r"),(41,53,"\u{1b}","\u{1b}"),
            (42,51,"\u{7f}","\u{7f}"),(43,48,"\t","\t"),(44,49," "," "),(45,27,"-","_"),
            (46,24,"=","+"),(47,33,"[","{"),(48,30,"]","}"),(49,42,"\\","|"),
            (51,41,";",":"),(52,39,"'","\""),(53,50,"`","~"),(54,43,",","<"),
            (55,47,".",">"),(56,44,"/","?"),
            (79,124,"\u{f703}","\u{f703}"),(80,123,"\u{f702}","\u{f702}"),
            (81,125,"\u{f701}","\u{f701}"),(82,126,"\u{f700}","\u{f700}")
        ]
        for (usage, code, plain, shifted) in punctuation { keys[usage] = Key(code: code, plain: plain, shifted: shifted) }
        return keys
    }()
}
#endif

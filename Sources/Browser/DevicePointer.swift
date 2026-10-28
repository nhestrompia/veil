import AppKit
import IOKit.hid
import IOKit.hidsystem

#if DEVICE_POINTER_EXPERIMENT
@MainActor
final class HardwarePointerOverlay: NSView {
    var point = CGPoint.zero { didSet { needsDisplay = true } }
    override var isFlipped: Bool { true }
    override func hitTest(_ point: NSPoint) -> NSView? { nil }
    override func isAccessibilityElement() -> Bool { false }
    override func draw(_ dirtyRect: NSRect) {
        let circle = NSBezierPath(ovalIn: CGRect(x: point.x - 8, y: point.y - 8, width: 16, height: 16))
        NSColor.black.setStroke()
        circle.lineWidth = 5
        circle.stroke()
        NSColor.systemGreen.setStroke()
        circle.lineWidth = 2
        circle.stroke()
    }
}

@MainActor
final class DevicePointerRouter {
    private let manager = IOHIDManagerCreate(kCFAllocatorDefault, IOOptionBits(kIOHIDOptionsTypeNone))
    private weak var window: NSWindow?
    private let overlay: HardwarePointerOverlay
    private var opened = false
    private var boundDevice: IOHIDDevice?
    private var profile: HIDPointerProfile?
    private var state = HardwarePointerState()
    private var geometry: CGRect?
    private var viewSize: CGSize?
    private var armedTime: Double?
    private var observers: [any NSObjectProtocol] = []
    private var timebase = mach_timebase_info_data_t()

    init(window: NSWindow, overlay: HardwarePointerOverlay) {
        self.window = window
        self.overlay = overlay
        mach_timebase_info(&timebase)
        for name in [NSWindow.didResignKeyNotification, NSWindow.didMoveNotification,
                     NSWindow.didResizeNotification, NSWindow.didChangeScreenNotification,
                     NSWindow.willMiniaturizeNotification] {
            observers.append(NotificationCenter.default.addObserver(forName: name, object: window, queue: .main) {
                [weak self] _ in MainActor.assumeIsolated { self?.cancel() }
            })
        }
        observers.append(NSWorkspace.shared.notificationCenter.addObserver(
            forName: NSWorkspace.willSleepNotification, object: nil, queue: .main) {
                [weak self] _ in MainActor.assumeIsolated { self?.cancel() }
            })
    }

    func start() {
        guard !opened, IOHIDCheckAccess(kIOHIDRequestTypeListenEvent) == kIOHIDAccessTypeGranted else { return }
        IOHIDManagerSetDeviceMatching(manager, [kIOHIDDeviceUsagePageKey: 1, kIOHIDDeviceUsageKey: 2] as CFDictionary)
        IOHIDManagerRegisterInputReportWithTimeStampCallback(manager, { context, result, sender, type, reportID, bytes, count, ticks in
            guard let context, let sender else { return }
            MainActor.assumeIsolated {
                let router = Unmanaged<DevicePointerRouter>.fromOpaque(context).takeUnretainedValue()
                // Apple's manager callback supplies the originating IOHIDDevice as sender.
                let device = Unmanaged<IOHIDDevice>.fromOpaque(sender).takeUnretainedValue()
                if let bound = router.boundDevice {
                    guard device == bound else { return }
                    if result != kIOReturnSuccess { router.cancel(); return }
                } else if result != kIOReturnSuccess { return }
                guard reportID == 1 || reportID == 2 else { return }
                router.receive(device, result: result, type: type, reportID: reportID, bytes: bytes, count: count, ticks: ticks)
            }
        }, Unmanaged.passUnretained(self).toOpaque())
        IOHIDManagerRegisterDeviceRemovalCallback(manager, { context, _, _, device in
            guard let context else { return }
            MainActor.assumeIsolated {
                let router = Unmanaged<DevicePointerRouter>.fromOpaque(context).takeUnretainedValue()
                if router.boundDevice == device { router.cancel() }
            }
        }, Unmanaged.passUnretained(self).toOpaque())
        IOHIDManagerScheduleWithRunLoop(manager, CFRunLoopGetMain(), CFRunLoopMode.commonModes.rawValue)
        let result = IOHIDManagerOpen(manager, IOOptionBits(kIOHIDOptionsTypeNone))
        opened = result == kIOReturnSuccess
        if !opened { IOHIDManagerUnscheduleFromRunLoop(manager, CFRunLoopGetMain(), CFRunLoopMode.commonModes.rawValue) }
        print("HARDWARE_POINTER opened=\(opened) nonexclusive=true ordinaryMouseEvents=false")
        fflush(stdout)
    }

    func arm() {
        cancel()
        guard opened, let window, window.isKeyWindow, window.isVisible,
              NSWorkspace.shared.frontmostApplication?.processIdentifier == getpid(),
              IOHIDCheckAccess(kIOHIDRequestTypeListenEvent) == kIOHIDAccessTypeGranted else { return }
        let now = seconds(mach_absolute_time())
        state.arm(size: overlay.bounds.size, now: now)
        armedTime = now
        geometry = window.frame
        viewSize = overlay.bounds.size
        overlay.point = state.position
        overlay.isHidden = false
        print("HARDWARE_POINTER armed=true requiresNeutralMovement=true systemCursorUsed=false")
        fflush(stdout)
    }

    func cancel() {
        if armedTime != nil { print("HARDWARE_POINTER armed=false") }
        state.cancel()
        armedTime = nil
        boundDevice = nil
        profile = nil
        geometry = nil
        viewSize = nil
        overlay.isHidden = true
        fflush(stdout)
    }

    func stop() {
        cancel()
        if opened {
            IOHIDManagerUnscheduleFromRunLoop(manager, CFRunLoopGetMain(), CFRunLoopMode.commonModes.rawValue)
            IOHIDManagerClose(manager, IOOptionBits(kIOHIDOptionsTypeNone))
            opened = false
        }
        for observer in observers {
            NotificationCenter.default.removeObserver(observer)
            NSWorkspace.shared.notificationCenter.removeObserver(observer)
        }
        observers.removeAll()
    }

    private func seconds(_ ticks: UInt64) -> Double {
        Double(ticks) * Double(timebase.numer) / Double(timebase.denom) / 1_000_000_000
    }

    private func receive(_ device: IOHIDDevice, result: IOReturn, type: IOHIDReportType,
                         reportID: UInt32, bytes: UnsafePointer<UInt8>, count: Int, ticks: UInt64) {
        guard let armedTime else { return }
        guard let window, window.isVisible, window.isKeyWindow,
              NSWorkspace.shared.frontmostApplication?.processIdentifier == getpid(),
              geometry == window.frame, viewSize == overlay.bounds.size,
              IOHIDCheckAccess(kIOHIDRequestTypeListenEvent) == kIOHIDAccessTypeGranted else {
            cancel()
            return
        }
        if let boundDevice, device != boundDevice { return }
        let selected: HIDPointerProfile
        if let profile { selected = profile }
        else {
            let source = HIDSourceSnapshot.observe(IOHIDDeviceGetService(device))
            guard let descriptor = IOHIDDeviceGetProperty(device, kIOHIDReportDescriptorKey as CFString) as? Data,
                  let found = HIDPointerProfile.evaluate(source, descriptor: descriptor) else {
                print("HARDWARE_POINTER sourceRefused=true")
                fflush(stdout)
                return
            }
            selected = found
        }
        // Vendor reports do not confer input authority or update the pointer.
        guard reportID == (selected == .builtInRelative ? 2 : 1) else { return }
        guard result == kIOReturnSuccess, type == kIOHIDReportTypeInput, count > 0, count <= 8 else {
            cancel()
            return
        }
        let time = seconds(ticks), now = seconds(mach_absolute_time())
        guard time > armedTime, time <= now, now - time <= 0.1 else { cancel(); return }
        guard let report = selected.decode(reportID: reportID,
            bytes: Array(UnsafeBufferPointer(start: bytes, count: count))) else { cancel(); return }
        if boundDevice == nil {
            guard !report.primaryDown, report.dx != 0 || report.dy != 0 else { return }
            boundDevice = device
            profile = selected
            print("HARDWARE_POINTER bound=true profile=\(selected.rawValue) humanAttested=false")
            fflush(stdout)
        }
        guard let update = state.receive(report, time: time, now: now) else { cancel(); return }
        overlay.point = update.position
        if let clickPosition = update.clickPosition, let app = NSApp as? DeviceKeyboardApplication {
            let point = overlay.convert(clickPosition, to: nil)
            app.dispatchDevicePointerClick(at: point, in: window)
        }
    }
}
#endif

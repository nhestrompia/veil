import AppKit
import IOKit.hid
import IOKit.hidsystem

#if VEIL_BROWSER
@MainActor
final class PhysicalMouseRouter {
    private let manager = IOHIDManagerCreate(kCFAllocatorDefault, IOOptionBits(kIOHIDOptionsTypeNone))
    private weak var window: NSWindow?
    private var opened = false
    private var boundDevice: IOHIDDevice?
    private var profile: HIDPointerProfile?
    private var state = PhysicalMouseState()
    private var beganAt: Double?
    private var geometry: CGRect?
    private var observers: [any NSObjectProtocol] = []
    private var timebase = mach_timebase_info_data_t()

    init(window: NSWindow) {
        self.window = window
        mach_timebase_info(&timebase)
        for name in [NSWindow.didResignKeyNotification, NSWindow.didMoveNotification,
                     NSWindow.didResizeNotification, NSWindow.didChangeScreenNotification,
                     NSWindow.willMiniaturizeNotification] {
            observers.append(NotificationCenter.default.addObserver(forName: name, object: window, queue: .main) {
                [weak self] _ in MainActor.assumeIsolated { self?.cancel() }
            })
        }
        observers.append(NotificationCenter.default.addObserver(forName: NSWindow.didBecomeKeyNotification,
            object: window, queue: .main) { [weak self] _ in MainActor.assumeIsolated { self?.beginSession() } })
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
                let router = Unmanaged<PhysicalMouseRouter>.fromOpaque(context).takeUnretainedValue()
                let device = Unmanaged<IOHIDDevice>.fromOpaque(sender).takeUnretainedValue()
                if let bound = router.boundDevice {
                    guard device == bound else { return }
                    if result != kIOReturnSuccess { router.cancel(); return }
                } else if result != kIOReturnSuccess { return }
                guard reportID == 1 || reportID == 2 else { return }
                router.receive(device, type: type, reportID: reportID, bytes: bytes, count: count, ticks: ticks)
            }
        }, Unmanaged.passUnretained(self).toOpaque())
        IOHIDManagerRegisterDeviceRemovalCallback(manager, { context, _, _, device in
            guard let context else { return }
            MainActor.assumeIsolated {
                let router = Unmanaged<PhysicalMouseRouter>.fromOpaque(context).takeUnretainedValue()
                if router.boundDevice == device { router.cancel() }
            }
        }, Unmanaged.passUnretained(self).toOpaque())
        IOHIDManagerScheduleWithRunLoop(manager, CFRunLoopGetMain(), CFRunLoopMode.commonModes.rawValue)
        opened = IOHIDManagerOpen(manager, IOOptionBits(kIOHIDOptionsTypeNone)) == kIOReturnSuccess
        if !opened { IOHIDManagerUnscheduleFromRunLoop(manager, CFRunLoopGetMain(), CFRunLoopMode.commonModes.rawValue) }
        beginSession()
        print("VEIL_MOUSE opened=\(opened) automatic=true cursor=system ordinaryEvents=false")
        fflush(stdout)
    }

    func cancel() {
        state.cancel()
        beganAt = nil
        geometry = nil
        boundDevice = nil
        profile = nil
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

    private func beginSession() {
        cancel()
        guard opened, let window, window.isVisible, window.isKeyWindow,
              NSWorkspace.shared.frontmostApplication?.processIdentifier == getpid() else { return }
        let now = seconds(mach_absolute_time())
        beganAt = now
        geometry = window.frame
        state.begin(now: now)
    }

    private func seconds(_ ticks: UInt64) -> Double {
        Double(ticks) * Double(timebase.numer) / Double(timebase.denom) / 1_000_000_000
    }

    private func receive(_ device: IOHIDDevice, type: IOHIDReportType, reportID: UInt32,
                         bytes: UnsafePointer<UInt8>, count: Int, ticks: UInt64) {
        guard opened, let window, window.isVisible, window.isKeyWindow,
              NSWorkspace.shared.frontmostApplication?.processIdentifier == getpid(),
              IOHIDCheckAccess(kIOHIDRequestTypeListenEvent) == kIOHIDAccessTypeGranted else { cancel(); return }
        guard beganAt != nil, geometry == window.frame else { beginSession(); return }
        if let boundDevice, boundDevice != device { return }
        let selected: HIDPointerProfile
        if let profile { selected = profile }
        else {
            let source = HIDSourceSnapshot.observe(IOHIDDeviceGetService(device))
            guard let descriptor = IOHIDDeviceGetProperty(device, kIOHIDReportDescriptorKey as CFString) as? Data,
                  let found = HIDPointerProfile.evaluate(source, descriptor: descriptor) else { return }
            selected = found
        }
        guard reportID == (selected == .usbRelative ? 1 : 2) else { return }
        guard type == kIOHIDReportTypeInput, count > 0, count <= 8 else { cancel(); return }
        let time = seconds(ticks), now = seconds(mach_absolute_time())
        guard let epoch = beganAt, time > epoch, time <= now, now - time <= 0.1,
              let report = PhysicalMouseReport.decode(profile: selected, reportID: reportID,
                  bytes: Array(UnsafeBufferPointer(start: bytes, count: count))) else { cancel(); return }
        if boundDevice == nil {
            guard !report.pointer.primaryDown,
                  report.pointer.dx != 0 || report.pointer.dy != 0 || report.wheel != 0 else { return }
            boundDevice = device
            profile = selected
            print("VEIL_MOUSE bound=true profile=\(selected.rawValue) cursor=system humanAttested=false")
            fflush(stdout)
        }
        // This coordinate is intentionally software-movable. The physical report,
        // not the cursor position, authorizes an action. Human-click redirection is in scope as a known limit.
        let point = window.convertPoint(fromScreen: NSEvent.mouseLocation)
        let inside = window.contentView.map { $0.bounds.contains($0.convert(point, from: nil)) } ?? false
        guard let update = state.receive(report, position: inside ? point : nil, time: time, now: now) else {
            if !state.isActive { cancel() }
            return
        }
        guard let app = NSApp as? DeviceKeyboardApplication else { return }
        if update.moved { app.dispatchDevicePointerMove(at: update.position, in: window) }
        guard beganAt == epoch, window.isKeyWindow, geometry == window.frame,
              NSWorkspace.shared.frontmostApplication?.processIdentifier == getpid() else { cancel(); return }
        if let click = update.clickPosition { app.dispatchDevicePointerClick(at: click, in: window) }
        if update.wheel != 0 { app.dispatchDeviceWheel(at: update.position, lines: update.wheel, in: window) }
    }
}
#endif

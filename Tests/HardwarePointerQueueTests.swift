import AppKit

@MainActor
final class PointerActionCounter: NSObject {
    var count = 0
    @objc func clicked(_ sender: Any?) { count += 1 }
}

@MainActor
final class NestedPointerView: NSView {
    var release: NSEvent?
    override func mouseDown(with event: NSEvent) {
        release = window?.nextEvent(matching: [.leftMouseUp, .leftMouseDragged],
            until: Date(timeIntervalSinceNow: 0.2), inMode: .eventTracking, dequeue: true)
    }
}

@main
enum HardwarePointerQueueTests {
    @MainActor static func main() {
        alarm(10)
        let app = DeviceKeyboardApplication.shared as! DeviceKeyboardApplication
        app.setActivationPolicy(.regular)
        app.finishLaunching()
        let window = AXBoundaryWindow(contentRect: NSRect(x: 120, y: 120, width: 400, height: 240),
            styleMask: [.titled, .closable], backing: .buffered, defer: false)
        window.title = "Hardware pointer dispatch checks"
        let button = NSButton(frame: NSRect(x: 100, y: 90, width: 180, height: 40))
        button.title = "Local diagnostic action"
        let counter = PointerActionCounter()
        button.target = counter
        button.action = #selector(PointerActionCounter.clicked(_:))
        window.contentView?.addSubview(button)
        window.makeKeyAndOrderFront(nil)
        app.activate(ignoringOtherApps: true)
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            runChecks(app, window: window, button: button, counter: counter)
            exit(0)
        }
        app.run()
    }

    @MainActor private static func runChecks(_ app: DeviceKeyboardApplication, window: AXBoundaryWindow,
                                             button: NSButton, counter: PointerActionCounter) {
        print("QUEUE_DIAGNOSTIC active=\(app.isActive) key=\(window.isKeyWindow) visible=\(window.isVisible)")
        func poison(_ type: NSEvent.EventType = .leftMouseUp) -> NSEvent {
            NSEvent.mouseEvent(with: type, location: CGPoint(x: 2, y: 2), modifierFlags: [],
                timestamp: ProcessInfo.processInfo.systemUptime, windowNumber: window.windowNumber,
                context: nil, eventNumber: 99, clickCount: 1, pressure: 0)!
        }
        app.postEvent(poison(), atStart: true)
        precondition(app.nextEvent(matching: .leftMouseUp, until: Date(timeIntervalSinceNow: 0.02),
            inMode: .default, dequeue: false) == nil, "Peeking must not expose or retain an untrusted release")
        app.postEvent(poison(), atStart: true)
        precondition(window.nextEvent(matching: .leftMouseUp, until: Date(timeIntervalSinceNow: 0.02),
            inMode: .eventTracking, dequeue: true) == nil, "Window tracking must use the queue gate")
        let tracking = NestedPointerView(frame: NSRect(x: 10, y: 10, width: 60, height: 60))
        window.contentView?.addSubview(tracking)
        app.postEvent(poison(.leftMouseDragged), atStart: true)
        app.postEvent(poison(), atStart: true)
        let point = CGPoint(x: 30, y: 30)
        app.dispatchDevicePointerClick(at: point, in: window)
        precondition(tracking.release?.type == .leftMouseUp)
        precondition(tracking.release?.locationInWindow == point, "Tracking must receive the exact private release")
        precondition(app.nextEvent(matching: [.leftMouseUp, .leftMouseDragged], until: Date(timeIntervalSinceNow: 0.02),
            inMode: .eventTracking, dequeue: true) == nil, "Poisoned events must remain refused after the click")
        app.postEvent(poison(), atStart: true)
        app.dispatchDevicePointerClick(at: CGPoint(x: 180, y: 110), in: window)
        precondition(counter.count == 1, "A native control must complete using only the private pair")
        precondition(app.nextEvent(matching: .leftMouseUp, until: Date(timeIntervalSinceNow: 0.02),
            inMode: .eventTracking, dequeue: true) == nil)
        app.sendEvent(poison(.leftMouseDown))
        precondition(counter.count == 1)
        window.orderOut(nil)
        print("Hardware pointer queue: direct and window tracking refuse untrusted events; private releases complete nested tracking and NSButton. No OS input posted, no device opened, no physical control.")
    }
}

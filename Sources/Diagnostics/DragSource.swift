import AppKit

@MainActor
final class DragSourceView: NSView, NSDraggingSource {
    private var sessionStarted = false
    override func acceptsFirstMouse(for event: NSEvent?) -> Bool { true }

    override func mouseDown(with event: NSEvent) {
        startDrag(with: event, origin: "posted-mouse")
    }

    func startDrag(with event: NSEvent, origin: String) {
        guard !sessionStarted else { return }
        sessionStarted = true
        let payload = NSPasteboardItem()
        payload.setString("native-input", forType: .string)
        let item = NSDraggingItem(pasteboardWriter: payload)
        let image = NSImage(size: NSSize(width: 60, height: 30))
        image.lockFocus()
        NSColor.systemPink.setFill()
        NSRect(x: 0, y: 0, width: 60, height: 30).fill()
        image.unlockFocus()
        item.setDraggingFrame(NSRect(x: 10, y: 25, width: 60, height: 30), contents: image)
        let session = beginDraggingSession(with: [item], event: event, source: self)
        session.animatesToStartingPositionsOnCancelOrFail = false
        print("DRAG_SOURCE began=true origin=\(origin)")
        fflush(stdout)
    }

    func draggingSession(_ session: NSDraggingSession, sourceOperationMaskFor context: NSDraggingContext) -> NSDragOperation { .copy }

    func draggingSession(_ session: NSDraggingSession, willBeginAt screenPoint: NSPoint) {
        print("DRAG_SOURCE beginCallback=true")
        fflush(stdout)
    }

    func draggingSession(_ session: NSDraggingSession, endedAt screenPoint: NSPoint, operation: NSDragOperation) {
        print("DRAG_SOURCE ended=true operation=\(operation.rawValue) x=\(screenPoint.x) y=\(screenPoint.y)")
        fflush(stdout)
    }
}

@MainActor
final class DragSourceController: NSObject, NSApplicationDelegate {
    private var window: NSWindow?

    func applicationDidFinishLaunching(_ notification: Notification) {
        let arguments = CommandLine.arguments
        guard let index = arguments.firstIndex(of: "--target-pid"), arguments.indices.contains(index + 1),
              let pid = pid_t(arguments[index + 1]),
              let target = NSRunningApplication(processIdentifier: pid),
              target.bundleIdentifier?.hasPrefix("research.agentfreebrowser.") == true else { NSApp.terminate(nil); return }
        let windows = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] ?? []
        guard let entry = windows.first(where: {
            ($0[kCGWindowOwnerPID as String] as? Int32) == pid && ($0[kCGWindowLayer as String] as? Int) == 0
        }), let bounds = entry[kCGWindowBounds as String] as? [String: Any],
           let frame = CGRect(dictionaryRepresentation: bounds as CFDictionary),
           let screen = NSScreen.screens.first else { NSApp.terminate(nil); return }
        let position = NSRect(x: frame.minX + 14, y: screen.frame.maxY - frame.minY - 270, width: 90, height: 90)
        let window = NSWindow(contentRect: position, styleMask: .titled, backing: .buffered, defer: false)
        window.title = "Disposable research drag source"
        window.isRestorable = false
        window.isOpaque = true
        window.backgroundColor = .systemPink
        window.level = NSWindow.Level(rawValue: NSWindow.Level.screenSaver.rawValue + 2)
        window.contentView = DragSourceView(frame: NSRect(origin: .zero, size: position.size))
        self.window = window
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        print("DRAG_SOURCE ready=true pid=\(getpid()) window=\(window.windowNumber)")
        fflush(stdout)
        if arguments.contains("--programmatic-start") {
            Task { @MainActor in
                try? await Task.sleep(for: .milliseconds(800))
                guard let view = window.contentView as? DragSourceView,
                      let event = NSEvent.mouseEvent(with: .leftMouseDown,
                        location: view.convert(NSPoint(x: view.bounds.midX, y: view.bounds.midY), to: nil),
                        modifierFlags: [], timestamp: ProcessInfo.processInfo.systemUptime,
                        windowNumber: window.windowNumber, context: nil, eventNumber: 1, clickCount: 1, pressure: 1) else { return }
                view.startDrag(with: event, origin: "programmatic-event")
            }
        }
    }
}

@main
enum DragSource {
    @MainActor static func main() {
        let app = NSApplication.shared
        let controller = DragSourceController()
        app.setActivationPolicy(.regular)
        app.delegate = controller
        withExtendedLifetime(controller) { app.run() }
    }
}

import AppKit

@MainActor
final class DragSourceView: NSView, NSDraggingSource {
    override func acceptsFirstMouse(for event: NSEvent?) -> Bool { true }

    override func mouseDown(with event: NSEvent) {
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
        print("DRAG_SOURCE began=true")
        fflush(stdout)
    }

    func draggingSession(_ session: NSDraggingSession, sourceOperationMaskFor context: NSDraggingContext) -> NSDragOperation { .copy }

    func draggingSession(_ session: NSDraggingSession, endedAt screenPoint: NSPoint, operation: NSDragOperation) {
        print("DRAG_SOURCE ended=true operation=\(operation.rawValue)")
        fflush(stdout)
    }
}

@main
enum DragSource {
    @MainActor static func main() {
        let arguments = CommandLine.arguments
        guard let index = arguments.firstIndex(of: "--target-pid"), arguments.indices.contains(index + 1),
              let pid = pid_t(arguments[index + 1]),
              let target = NSRunningApplication(processIdentifier: pid),
              target.bundleIdentifier?.hasPrefix("research.agentfreebrowser.") == true else { return }
        let windows = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] ?? []
        guard let entry = windows.first(where: {
            ($0[kCGWindowOwnerPID as String] as? Int32) == pid && ($0[kCGWindowLayer as String] as? Int) == 0
        }), let bounds = entry[kCGWindowBounds as String] as? [String: Any],
           let frame = CGRect(dictionaryRepresentation: bounds as CFDictionary) else { return }
        let app = NSApplication.shared
        app.setActivationPolicy(.regular)
        guard let screen = NSScreen.screens.first else { return }
        let position = NSRect(x: frame.minX + 14, y: screen.frame.maxY - frame.minY - 270, width: 90, height: 90)
        let window = NSWindow(contentRect: position, styleMask: .borderless, backing: .buffered, defer: false)
        window.title = "Disposable research drag source"
        window.isOpaque = true
        window.backgroundColor = .systemPink
        window.level = .screenSaver
        window.contentView = DragSourceView(frame: NSRect(origin: .zero, size: position.size))
        window.makeKeyAndOrderFront(nil)
        app.activate(ignoringOtherApps: true)
        print("DRAG_SOURCE ready=true pid=\(getpid()) window=\(window.windowNumber)")
        fflush(stdout)
        withExtendedLifetime(window) { app.run() }
    }
}

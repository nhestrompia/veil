import AppKit

@MainActor
final class FixedGeometryWindow: NSWindow {
    private var pinnedFrame: NSRect?

    func pinGeometry() {
        guard pinnedFrame == nil else { return }
        pinnedFrame = frame
        isMovable = false
        minSize = frame.size
        maxSize = frame.size
        print("GEOMETRY_POLICY pinned=true")
        fflush(stdout)
    }

    private func refuses(_ operation: String, frame proposed: NSRect? = nil) -> Bool {
        guard let pinnedFrame, proposed != pinnedFrame else { return false }
        print("GEOMETRY_POLICY refused=\(operation)")
        fflush(stdout)
        return true
    }

    override func setFrame(_ frameRect: NSRect, display flag: Bool) {
        guard !refuses("set-frame", frame: frameRect) else { return }
        super.setFrame(frameRect, display: flag)
    }

    override func setFrame(_ frameRect: NSRect, display flag: Bool, animate: Bool) {
        guard !refuses("animate-frame", frame: frameRect) else { return }
        super.setFrame(frameRect, display: flag, animate: animate)
    }

    override func setFrameOrigin(_ point: NSPoint) {
        guard pinnedFrame == nil || point == pinnedFrame?.origin else {
            _ = refuses("set-origin")
            return
        }
        super.setFrameOrigin(point)
    }

    override func zoom(_ sender: Any?) {
        guard !refuses("zoom") else { return }
        super.zoom(sender)
    }

    override func performZoom(_ sender: Any?) {
        guard !refuses("perform-zoom") else { return }
        super.performZoom(sender)
    }

    override func toggleFullScreen(_ sender: Any?) {
        guard !refuses("fullscreen") else { return }
        super.toggleFullScreen(sender)
    }
}

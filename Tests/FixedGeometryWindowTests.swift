import AppKit

@main
@MainActor
enum FixedGeometryWindowTests {
    static func main() {
        let app = NSApplication.shared
        app.setActivationPolicy(.prohibited)
        let window = FixedGeometryWindow(contentRect: NSRect(x: 100, y: 100, width: 800, height: 600),
                                         styleMask: [.titled, .resizable], backing: .buffered, defer: false)
        window.isReleasedWhenClosed = false
        let original = window.frame
        var changed = original
        changed.size.width += 100
        window.setFrame(changed, display: false)
        precondition(window.frame == changed, "The ordinary resize control must work")
        window.setFrameOrigin(NSPoint(x: 150, y: 150))
        precondition(window.frame.origin == NSPoint(x: 150, y: 150), "The ordinary move control must work")
        window.pinGeometry()
        let pinned = window.frame
        let attempts: [(String, () -> Void)] = [
            ("direct-frame", { window.setFrame(original, display: false) }),
            ("animated-frame", { window.setFrame(original, display: false, animate: true) }),
            ("origin", { window.setFrameOrigin(.zero) }),
            ("top-left", { window.setFrameTopLeftPoint(.zero) }),
            ("content-size", { window.setContentSize(NSSize(width: 700, height: 500)) }),
            ("zoom", { window.zoom(nil) }),
            ("perform-zoom", { window.performZoom(nil) }),
            ("fullscreen", { window.toggleFullScreen(nil) })
        ]
        for (name, attempt) in attempts {
            attempt()
            precondition(window.frame == pinned, "Pinned geometry changed through \(name)")
            precondition(!window.styleMask.contains(.fullScreen), "Fullscreen bypassed the frame policy")
        }
        window.setFrame(pinned, display: false)
        window.pinGeometry()
        precondition(window.frame == pinned)
        window.close()
        print("Fixed geometry AppKit controls passed: ordinary move/resize and eight pinned operations. No external attack or window was displayed.")
    }
}

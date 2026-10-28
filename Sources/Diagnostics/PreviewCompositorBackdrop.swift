import AppKit

@MainActor
enum PreviewCompositorBackdrop {
    static let level = NSWindow.Level(rawValue: -1)

    static func make(frame: CGRect) -> NSPanel {
        let panel = NSPanel(contentRect: frame, styleMask: [.borderless, .nonactivatingPanel],
                            backing: .buffered, defer: false)
        panel.hidesOnDeactivate = false
        panel.animationBehavior = .none
        panel.collectionBehavior = [.canJoinAllSpaces, .canJoinAllApplications, .fullScreenAuxiliary]
        panel.level = level
        return panel
    }
}

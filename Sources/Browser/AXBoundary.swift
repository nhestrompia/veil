import AppKit
import WebKit

#if AX_BOUNDARY_EXPERIMENT
@MainActor
final class AXBoundaryApplication: NSApplication {
    override func accessibilityChildren() -> [Any]? { [] }
    override func accessibilityWindows() -> [Any]? { [] }
    override func accessibilityFocusedWindow() -> Any? { nil }
    override var accessibilityFocusedUIElement: Any? { nil }
    override func accessibilityHitTest(_ point: NSPoint) -> Any? { nil }
    override func isAccessibilitySelectorAllowed(_ selector: Selector) -> Bool { false }
}

@MainActor
final class AXBoundaryWindow: NSWindow {
    override func accessibilityChildren() -> [Any]? { [] }
    override var accessibilityFocusedUIElement: Any? { nil }
    override func accessibilityHitTest(_ point: NSPoint) -> Any? { nil }
    override func isAccessibilitySelectorAllowed(_ selector: Selector) -> Bool { false }
}

@MainActor
final class AXBoundaryWebView: WKWebView {
    override func accessibilityChildren() -> [Any]? { [] }
    override var accessibilityFocusedUIElement: Any? { nil }
    override func accessibilityHitTest(_ point: NSPoint) -> Any? { nil }
    override func isAccessibilitySelectorAllowed(_ selector: Selector) -> Bool { false }
}
#endif

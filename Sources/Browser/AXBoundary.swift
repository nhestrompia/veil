import AppKit
import WebKit

#if AX_BOUNDARY_EXPERIMENT || DEVICE_KEYBOARD_EXPERIMENT
@MainActor
class AXBoundaryApplication: NSApplication {
    override func accessibilityChildren() -> [Any]? { [] }
    override func accessibilityWindows() -> [Any]? { [] }
    override func accessibilityFocusedWindow() -> Any? { nil }
    override var accessibilityFocusedUIElement: Any? { nil }
    override func accessibilityHitTest(_ point: NSPoint) -> Any? { nil }
    override func isAccessibilitySelectorAllowed(_ selector: Selector) -> Bool { false }
}

@MainActor
final class AXBoundaryWindow: NSWindow {
    #if DEVICE_KEYBOARD_EXPERIMENT
    private var deviceFieldEditor: DeviceFieldEditor?

    override func fieldEditor(_ create: Bool, for object: Any?) -> NSText? {
        guard object is DeviceAddressField else { return super.fieldEditor(create, for: object) }
        if deviceFieldEditor == nil, create {
            let editor = DeviceFieldEditor(frame: .zero)
            editor.isFieldEditor = true
            editor.isRichText = false
            if #available(macOS 15.0, *) { editor.writingToolsBehavior = .none }
            deviceFieldEditor = editor
        }
        return deviceFieldEditor
    }
    #endif

    override func accessibilityChildren() -> [Any]? { [] }
    override var accessibilityFocusedUIElement: Any? { nil }
    override func accessibilityHitTest(_ point: NSPoint) -> Any? { nil }
    override func isAccessibilitySelectorAllowed(_ selector: Selector) -> Bool { false }
}

#if DEVICE_KEYBOARD_EXPERIMENT
extension AXBoundaryWindow: NSDraggingDestination {
    func draggingEntered(_ sender: any NSDraggingInfo) -> NSDragOperation { DeviceDragGate.refuseOperation("window.entered") }
    func draggingUpdated(_ sender: any NSDraggingInfo) -> NSDragOperation { DeviceDragGate.refuseOperation("window.updated") }
    func prepareForDragOperation(_ sender: any NSDraggingInfo) -> Bool { DeviceDragGate.refuseImport("window.prepare") }
    func performDragOperation(_ sender: any NSDraggingInfo) -> Bool { DeviceDragGate.refuseImport("window.perform") }
}
#endif

@MainActor
final class AXBoundaryWebView: RestrictedWebView {
    #if DEVICE_KEYBOARD_EXPERIMENT
    override func draggingEntered(_ sender: any NSDraggingInfo) -> NSDragOperation { DeviceDragGate.refuseOperation("web.entered") }
    override func draggingUpdated(_ sender: any NSDraggingInfo) -> NSDragOperation { DeviceDragGate.refuseOperation("web.updated") }
    override func prepareForDragOperation(_ sender: any NSDraggingInfo) -> Bool { DeviceDragGate.refuseImport("web.prepare") }
    override func performDragOperation(_ sender: any NSDraggingInfo) -> Bool { DeviceDragGate.refuseImport("web.perform") }
    #endif

    override func accessibilityChildren() -> [Any]? { [] }
    override var accessibilityFocusedUIElement: Any? { nil }
    override func accessibilityHitTest(_ point: NSPoint) -> Any? { nil }
    override func isAccessibilitySelectorAllowed(_ selector: Selector) -> Bool { false }
}
#endif

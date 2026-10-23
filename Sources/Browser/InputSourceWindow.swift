import AppKit

@MainActor
final class InputSourceWindow: NSWindow {
    override func sendEvent(_ event: NSEvent) {
        switch event.type {
        case .leftMouseDown, .rightMouseDown, .otherMouseDown, .keyDown, .scrollWheel:
            let source = event.cgEvent?.getIntegerValueField(.eventSourceStateID)
            guard source == Int64(CGEventSourceStateID.hidSystemState.rawValue) else {
                print("INPUT_GATE_REFUSED source=\(source.map(String.init) ?? "nil") type=\(event.type.rawValue)")
                fflush(stdout)
                return
            }
            print("INPUT_GATE_ACCEPTED source=\(source.map(String.init) ?? "nil") type=\(event.type.rawValue)")
            fflush(stdout)
        default:
            break
        }
        super.sendEvent(event)
    }
}

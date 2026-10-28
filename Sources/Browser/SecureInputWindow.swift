import AppKit
import Carbon

@MainActor
final class SecureInputWindow: NSWindow {
    override func sendEvent(_ event: NSEvent) {
        if event.type == .keyDown || event.type == .leftMouseDown {
            print("SECURE_INPUT_EVENT type=\(event.type.rawValue) effective=\(IsSecureEventInputEnabled())")
            fflush(stdout)
        }
        super.sendEvent(event)
    }
}

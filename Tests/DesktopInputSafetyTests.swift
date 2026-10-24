import CoreGraphics
import Foundation

@main
enum DesktopInputSafetyTests {
    static func main() throws {
        var tap = CGEventTapInformation()
        tap.enabled = true
        tap.options = .defaultTap
        tap.eventsOfInterest = 1 << CGEventType.leftMouseDown.rawValue
        precondition(DesktopInputSafety.blocksMouse(tap))
        tap.options = .listenOnly
        precondition(!DesktopInputSafety.blocksMouse(tap))
        tap.options = .defaultTap
        tap.enabled = false
        precondition(!DesktopInputSafety.blocksMouse(tap))
        tap.enabled = true
        tap.eventsOfInterest = 1 << CGEventType.keyDown.rawValue
        precondition(!DesktopInputSafety.blocksMouse(tap))
        tap.eventsOfInterest = 1 << CGEventType.leftMouseUp.rawValue
        precondition(DesktopInputSafety.blocksMouse(tap))
        for safety in [DesktopInputSafety(available: false, blockingOwners: []),
                       DesktopInputSafety(available: true, blockingOwners: [123])] {
            do {
                try safety.requireIsolatedMouse()
                preconditionFailure("Unsafe mouse input was permitted")
            } catch is InputSafetyFailure {}
        }
        try DesktopInputSafety(available: true, blockingOwners: []).requireIsolatedMouse()
        print("Desktop input safety checks passed")
        print("Current read-only status: \(DesktopInputSafety.observe().report)")
    }
}

import CoreGraphics
import Foundation

struct DesktopInputSafety {
    let available: Bool
    let blockingOwners: [pid_t]

    var report: [String: Any] {
        ["available": available, "blockingMouseHookPIDs": blockingOwners]
    }

    static func blocksMouse(_ tap: CGEventTapInformation) -> Bool {
        let mouseTypes: [CGEventType] = [.leftMouseDown, .leftMouseUp, .rightMouseDown, .rightMouseUp,
            .mouseMoved, .leftMouseDragged, .rightMouseDragged, .otherMouseDown, .otherMouseUp, .otherMouseDragged]
        let mask = mouseTypes.reduce(CGEventMask(0)) { $0 | (CGEventMask(1) << $1.rawValue) }
        return tap.enabled && tap.options == .defaultTap && tap.eventsOfInterest & mask != 0
    }

    static func observe() -> DesktopInputSafety {
        var count: UInt32 = 0
        guard CGGetEventTapList(0, nil, &count) == .success else {
            return DesktopInputSafety(available: false, blockingOwners: [])
        }
        var taps = [CGEventTapInformation](repeating: CGEventTapInformation(), count: Int(count))
        let capacity = count
        guard CGGetEventTapList(capacity, &taps, &count) == .success, count <= capacity else {
            return DesktopInputSafety(available: false, blockingOwners: [])
        }
        let owners = Set(taps.prefix(Int(count)).filter(blocksMouse).map(\.tappingProcess))
        return DesktopInputSafety(available: true, blockingOwners: owners.sorted())
    }

    func requireIsolatedMouse() throws {
        guard available && blockingOwners.isEmpty else {
            throw InputSafetyFailure(description: "Desktop input refused: mouse-hook observation is unavailable or modifying hooks are active. Owners: \(blockingOwners)")
        }
    }
}

struct InputSafetyFailure: Error, CustomStringConvertible {
    let description: String
}

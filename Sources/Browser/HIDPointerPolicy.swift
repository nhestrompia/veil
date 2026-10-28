import Foundation
import CryptoKit
import CoreGraphics

enum HIDPointerProfile: String {
    case builtInRelative
    case usbRelative

    var descriptorSHA256: String {
        switch self {
        case .builtInRelative: "736a3fca9f16530aa4301ed3ec8494c19deccb013bffcd1efefc86c1c02a938a"
        case .usbRelative: "c3b164b26e4b806cc17c6d8fd6d5a9daebf40e301a4ad6183d733b130675b386"
        }
    }

    static func evaluate(_ source: HIDSourceSnapshot, descriptor: Data) -> Self? {
        guard source.observationValid, !source.softwareAncestor, source.virtualDevice != true,
              source.primaryUsagePage == 1, source.primaryUsage == 2 else { return nil }
        let builtIn = ["AppleHIDTransportHIDDevice", "AppleHIDTransportInterface",
                       "AppleHIDTransportProtocolSCMFIFO", "AppleHIDTransportDeviceFIFO",
                       "AppleDockChannelDevice", "AppleDockChannel"]
        let usb = ["AppleUserHIDDevice", "IOUSBHostInterface", "IOUSBHostDevice",
                   "AppleUSB20HubPort", "AppleUSB20Hub", "IOUSBHostDevice",
                   "AppleUSB20XHCIARMPort", "AppleT8142USBXHCI"]
        let profile: Self
        if source.transport == "FIFO", source.serviceClasses.starts(with: builtIn) {
            profile = .builtInRelative
        } else if source.transport == "USB", source.serviceClasses.starts(with: usb) {
            profile = .usbRelative
        } else { return nil }
        let digest = SHA256.hash(data: descriptor).map { String(format: "%02x", $0) }.joined()
        return digest == profile.descriptorSHA256 ? profile : nil
    }

    func decode(reportID: UInt32, bytes: [UInt8]) -> HIDPointerReport? {
        // These layouts are pinned to the two separately measured descriptors.
        switch self {
        case .builtInRelative:
            guard reportID == 2, bytes.count == 8, bytes[0] == 2, bytes[1] & 0xfe == 0,
                  bytes[4...7].allSatisfy({ $0 == 0 }) else { return nil }
            let x = Int(Int8(bitPattern: bytes[2])), y = Int(Int8(bitPattern: bytes[3]))
            guard x != -128, y != -128 else { return nil }
            return HIDPointerReport(dx: x, dy: y, primaryDown: bytes[1] == 1)
        case .usbRelative:
            guard reportID == 1, bytes.count == 7, bytes[0] == 1, bytes[1] & 0xfe == 0,
                  bytes[6] == 0 else { return nil }
            let x = Int(Int16(bitPattern: UInt16(bytes[2]) | UInt16(bytes[3]) << 8))
            let y = Int(Int16(bitPattern: UInt16(bytes[4]) | UInt16(bytes[5]) << 8))
            guard x != -32768, y != -32768 else { return nil }
            return HIDPointerReport(dx: x, dy: y, primaryDown: bytes[1] == 1)
        }
    }
}

struct HIDPointerReport {
    let dx: Int
    let dy: Int
    let primaryDown: Bool
}

struct HardwarePointerState {
    struct Update {
        let position: CGPoint
        let clickPosition: CGPoint?
        var click: Bool { clickPosition != nil }
    }
    private struct Press {
        let position: CGPoint
        let time: Double
    }
    private(set) var position = CGPoint.zero
    private var bounds = CGSize.zero
    private var armedAt: Double?
    private var lastTime: Double = 0
    private var press: Press?
    private var primaryDown = false
    private var neutralSeen = false

    mutating func arm(size: CGSize, now: Double) {
        cancel()
        guard size.width.isFinite, size.height.isFinite, size.width >= 2, size.height >= 2,
              now.isFinite else { return }
        bounds = size
        position = CGPoint(x: size.width / 2, y: size.height / 2)
        armedAt = now
        lastTime = now
    }

    mutating func cancel() {
        armedAt = nil
        press = nil
        primaryDown = false
        neutralSeen = false
    }

    mutating func receive(_ report: HIDPointerReport, time: Double, now: Double) -> Update? {
        guard let armedAt, time.isFinite, now.isFinite, time > armedAt, time > lastTime,
              time <= now, now - time <= 0.1,
              abs(Double(report.dx)) <= 4096, abs(Double(report.dy)) <= 4096 else {
            cancel()
            return nil
        }
        lastTime = time
        // A held button cannot carry authority into a new session.
        if !neutralSeen {
            guard !report.primaryDown else { return nil }
            neutralSeen = true
        }
        position.x = min(max(position.x + Double(report.dx), 1), bounds.width - 1)
        position.y = min(max(position.y + Double(report.dy), 1), bounds.height - 1)
        if let press, hypot(position.x - press.position.x, position.y - press.position.y) > 4 {
            self.press = nil
        }
        var clickPosition: CGPoint?
        if report.primaryDown, !primaryDown {
            press = Press(position: position, time: time)
        } else if !report.primaryDown, primaryDown {
            if let press, time - press.time <= 2 { clickPosition = press.position }
            press = nil
        }
        primaryDown = report.primaryDown
        return Update(position: position, clickPosition: clickPosition)
    }
}

import Foundation
import CoreGraphics

struct PhysicalMouseReport {
    let pointer: HIDPointerReport
    let wheel: Int

    static func decode(profile: HIDPointerProfile, reportID: UInt32, bytes: [UInt8]) -> Self? {
        var pointerBytes = bytes
        let wheel: Int
        switch profile {
        case .usbRelative:
            guard bytes.count == 7 else { return nil }
            wheel = Int(Int8(bitPattern: bytes[6]))
            guard wheel != -128 else { return nil }
            pointerBytes[6] = 0
        case .builtInRelative:
            wheel = 0
        }
        guard let pointer = profile.decode(reportID: reportID, bytes: pointerBytes) else { return nil }
        return Self(pointer: pointer, wheel: wheel)
    }
}

struct PhysicalMouseState {
    struct Update {
        let position: CGPoint
        let moved: Bool
        let clickPosition: CGPoint?
        let wheel: Int
    }

    private struct Press {
        let position: CGPoint
        let time: Double
    }

    private var beganAt: Double?
    private var lastTime: Double = 0
    private var neutralSeen = false
    private var down = false
    private var press: Press?
    var isActive: Bool { beganAt != nil }

    mutating func begin(now: Double) {
        self = Self()
        if now.isFinite {
            beganAt = now
            lastTime = now
        }
    }

    mutating func cancel() { self = Self() }

    mutating func receive(_ report: PhysicalMouseReport, position: CGPoint?, time: Double, now: Double) -> Update? {
        guard let beganAt, time.isFinite, now.isFinite, time > beganAt, time > lastTime,
              time <= now, now - time <= 0.1, abs(Double(report.pointer.dx)) <= 4096,
              abs(Double(report.pointer.dy)) <= 4096, (-127...127).contains(report.wheel) else {
            cancel()
            return nil
        }
        lastTime = time
        let wasDown = down
        down = report.pointer.primaryDown
        if !neutralSeen {
            guard !down else { return nil }
            neutralSeen = true
        }
        guard let position, position.x.isFinite, position.y.isFinite else {
            press = nil
            return nil
        }
        if let press, hypot(position.x - press.position.x, position.y - press.position.y) > 4 {
            self.press = nil
        }
        var clickPosition: CGPoint?
        if report.wheel != 0 {
            press = nil
        } else if down, !wasDown {
            press = Press(position: position, time: time)
        } else if !down, wasDown {
            if let press, time - press.time <= 2 { clickPosition = press.position }
            press = nil
        }
        return Update(position: position, moved: report.pointer.dx != 0 || report.pointer.dy != 0,
                      clickPosition: clickPosition, wheel: !down && !wasDown ? report.wheel : 0)
    }
}

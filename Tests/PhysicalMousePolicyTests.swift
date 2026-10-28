import Foundation
import CoreGraphics

@main
enum PhysicalMousePolicyTests {
    static func main() {
        func packet(_ wheel: UInt8 = 0) -> [UInt8] { [1, 0, 0, 0, 0, 0, wheel] }
        precondition(PhysicalMouseReport.decode(profile: .usbRelative, reportID: 1, bytes: packet(1))?.wheel == 1)
        precondition(PhysicalMouseReport.decode(profile: .usbRelative, reportID: 1, bytes: packet(255))?.wheel == -1)
        precondition(PhysicalMouseReport.decode(profile: .usbRelative, reportID: 1, bytes: packet(128)) == nil)
        for count in 0..<7 {
            precondition(PhysicalMouseReport.decode(profile: .usbRelative, reportID: 1,
                bytes: Array(packet().prefix(count))) == nil)
        }
        var secondary = packet(1)
        secondary[1] = 2
        precondition(PhysicalMouseReport.decode(profile: .usbRelative, reportID: 1, bytes: secondary) == nil)
        // The frozen independent-pointer decoder must still refuse wheels.
        precondition(HIDPointerProfile.usbRelative.decode(reportID: 1, bytes: packet(1)) == nil)
        func report(down: Bool = false, dx: Int = 0, wheel: Int = 0) -> PhysicalMouseReport {
            PhysicalMouseReport(pointer: HIDPointerReport(dx: dx, dy: 0, primaryDown: down), wheel: wheel)
        }
        let point = CGPoint(x: 30, y: 40)
        var state = PhysicalMouseState()
        state.begin(now: 1)
        precondition(state.receive(report(down: true), position: point, time: 1.01, now: 1.01) == nil)
        precondition(state.receive(report(), position: point, time: 1.02, now: 1.02)?.clickPosition == nil)
        _ = state.receive(report(down: true), position: point, time: 1.03, now: 1.03)
        precondition(state.receive(report(), position: point, time: 1.04, now: 1.04)?.clickPosition == point)
        precondition(state.receive(report(wheel: -3), position: point, time: 1.05, now: 1.05)?.wheel == -3)
        _ = state.receive(report(down: true), position: point, time: 1.06, now: 1.06)
        _ = state.receive(report(down: true, wheel: 1), position: point, time: 1.07, now: 1.07)
        precondition(state.receive(report(), position: point, time: 1.08, now: 1.08)?.clickPosition == nil)
        _ = state.receive(report(down: true), position: point, time: 1.09, now: 1.09)
        _ = state.receive(report(down: true), position: nil, time: 1.10, now: 1.10)
        precondition(state.receive(report(), position: point, time: 1.11, now: 1.11)?.clickPosition == nil)
        _ = state.receive(report(down: true), position: point, time: 1.12, now: 1.12)
        precondition(state.receive(report(), position: CGPoint(x: 90, y: 90), time: 1.13, now: 1.13)?.clickPosition == nil)
        state.cancel()
        precondition(state.receive(report(wheel: 1), position: point, time: 1.14, now: 1.14) == nil)
        for invalid in [Double.nan, 0.9, 1.0, 1.2] {
            state.begin(now: 1)
            precondition(state.receive(report(), position: point, time: invalid, now: 1.1) == nil)
        }
        state.begin(now: 1)
        precondition(state.receive(report(), position: point, time: 1.01, now: 1.2) == nil)
        print("Physical mouse policy passed: signed wheel, neutral start, click pairing, bounds, cancellation, and stale reports. Fabricated reports only.")
    }
}

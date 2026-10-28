import Foundation
import CoreGraphics

@main
@MainActor
enum HardwarePointerAdversarialTests {
    static var failures = [String]()
    static var checks = 0

    static func check(_ condition: @autoclosure () -> Bool, _ message: String) {
        checks += 1
        if !condition() { failures.append(message) }
    }

    static func report(_ x: Int = 0, _ y: Int = 0, _ down: Bool = false) -> HIDPointerReport {
        HIDPointerReport(dx: x, dy: y, primaryDown: down)
    }

    static func main() throws {
        let evidence = try JSONSerialization.jsonObject(with: Data(contentsOf:
            URL(fileURLWithPath: "docs/evidence/hardware-pointer-source-audit.json"))) as! [String: Any]
        for row in evidence["devices"] as! [[String: Any]] {
            let hex = row["reportDescriptor"] as! String
            let bytes = stride(from: 0, to: hex.count, by: 2).map { offset in
                let index = hex.index(hex.startIndex, offsetBy: offset)
                return UInt8(hex[index..<hex.index(index, offsetBy: 2)], radix: 16)!
            }
            let source = HIDSourceSnapshot(serviceClasses: row["serviceClasses"] as! [String],
                transport: row["transport"] as? String, virtualDevice: nil,
                primaryUsagePage: 1, primaryUsage: 2, softwareAncestor: false, observationValid: true)
            check(HIDPointerProfile.evaluate(source, descriptor: Data(bytes)) != nil, "measured descriptor must be admitted")
            for index in bytes.indices {
                var mutated = bytes
                mutated[index] ^= 1
                check(HIDPointerProfile.evaluate(source, descriptor: Data(mutated)) == nil,
                      "descriptor byte \(index) mutation must be refused")
            }
        }
        for (profile, id, packet) in [(HIDPointerProfile.builtInRelative, UInt32(2), [UInt8](arrayLiteral: 2, 0, 0, 0, 0, 0, 0, 0)),
                                      (.usbRelative, UInt32(1), [UInt8](arrayLiteral: 1, 0, 0, 0, 0, 0, 0))] {
            var wrongID = packet
            wrongID[0] ^= 3
            check(profile.decode(reportID: id, bytes: wrongID) == nil, "header ID disagreement must be refused")
            for value in 0...255 {
                var otherButton = packet
                otherButton[1] = UInt8(value)
                check((profile.decode(reportID: id, bytes: otherButton) != nil) == (value == 0 || value == 1),
                      "only primary button encoding may pass")
            }
            for index in (profile == .builtInRelative ? 4..<8 : 6..<7) {
                for value in 1...255 {
                    var reserved = packet
                    reserved[index] = UInt8(value)
                    check(profile.decode(reportID: id, bytes: reserved) == nil, "reserved or wheel data must be refused")
                }
            }
        }
        var fifoMin = [UInt8](arrayLiteral: 2, 0, 128, 0, 0, 0, 0, 0)
        check(HIDPointerProfile.builtInRelative.decode(reportID: 2, bytes: fifoMin) == nil, "FIFO out-of-range X")
        fifoMin[2] = 0; fifoMin[3] = 128
        check(HIDPointerProfile.builtInRelative.decode(reportID: 2, bytes: fifoMin) == nil, "FIFO out-of-range Y")
        check(HIDPointerProfile.usbRelative.decode(reportID: 1, bytes: [1, 0, 0, 128, 0, 0, 0]) == nil, "USB out-of-range X")
        check(HIDPointerProfile.usbRelative.decode(reportID: 1, bytes: [1, 0, 0, 0, 0, 128, 0]) == nil, "USB out-of-range Y")

        var state = HardwarePointerState()
        func arm() { state.arm(size: CGSize(width: 100, height: 100), now: 1) }
        func send(_ r: HIDPointerReport, _ t: Double) -> HardwarePointerState.Update? {
            state.receive(r, time: t, now: t)
        }
        arm()
        _ = send(report(), 1.01)
        _ = send(report(0, 0, true), 1.02)
        _ = send(report(5, 0, true), 1.03)
        _ = send(report(-5, 0, true), 1.04)
        check(send(report(), 1.05)?.click == false, "moving away and back must not restore canceled press")
        arm()
        _ = send(report(), 1.01)
        _ = send(report(0, 0, true), 1.02)
        check(state.receive(report(), time: 1.02, now: 1.03) == nil, "duplicate timestamp must disarm")
        check(send(report(), 1.04) == nil, "disarmed state must stay disarmed")
        arm()
        _ = send(report(), 1.01)
        _ = send(report(0, 0, true), 1.02)
        check(send(report(), 3.03)?.click == false, "release after timeout must not click")
        arm()
        _ = send(report(), 1.01)
        _ = send(report(0, 0, true), 1.02)
        let changedTarget = send(report(4, 0), 1.03)
        check(changedTarget?.clickPosition == CGPoint(x: 50, y: 50),
              "small movement must preserve the press point instead of retargeting the click")
        check(changedTarget?.position == CGPoint(x: 54, y: 50), "the visible pointer still follows accepted motion")
        arm()
        _ = send(report(), 1.01)
        _ = send(report(0, 0, true), 1.02)
        state.cancel()
        state.arm(size: CGSize(width: 100, height: 100), now: 2)
        check(state.receive(report(), time: 2.01, now: 2.01)?.click == false, "release after rearm must not complete previous press")
        state.arm(size: CGSize(width: CGFloat.nan, height: 100), now: 3)
        check(state.receive(report(), time: 3.01, now: 3.01) == nil, "invalid geometry must disarm")
        if failures.isEmpty {
            print("PASS: \(checks) offline adversarial pointer checks")
        } else {
            for failure in failures { print("FAIL: \(failure)") }
            print("\(failures.count) failures across \(checks) offline adversarial pointer checks")
            exit(1)
        }
    }
}

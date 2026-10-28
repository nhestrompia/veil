import Foundation
import CoreGraphics

@main
enum HardwarePointerPolicyTests {
    static func main() throws {
        let evidence = try JSONSerialization.jsonObject(with: Data(contentsOf:
            URL(fileURLWithPath: "docs/evidence/hardware-pointer-source-audit.json"))) as! [String: Any]
        for row in evidence["devices"] as! [[String: Any]] {
            let hex = row["reportDescriptor"] as! String
            let descriptor = Data(stride(from: 0, to: hex.count, by: 2).map { index in
                let start = hex.index(hex.startIndex, offsetBy: index)
                return UInt8(hex[start..<hex.index(start, offsetBy: 2)], radix: 16)!
            })
            let source = HIDSourceSnapshot(serviceClasses: row["serviceClasses"] as! [String],
                transport: row["transport"] as? String, virtualDevice: row["virtualDevice"] as? Bool,
                primaryUsagePage: row["primaryUsagePage"] as? Int, primaryUsage: row["primaryUsage"] as? Int,
                softwareAncestor: false, observationValid: true)
            precondition(HIDPointerProfile.evaluate(source, descriptor: descriptor) != nil)
            func modified(classes: [String]? = nil, transport: String? = nil, virtual: Bool = false,
                          software: Bool = false, valid: Bool = true, usage: Int = 2) -> HIDSourceSnapshot {
                HIDSourceSnapshot(serviceClasses: classes ?? source.serviceClasses,
                    transport: transport ?? source.transport, virtualDevice: virtual,
                    primaryUsagePage: 1, primaryUsage: usage, softwareAncestor: software, observationValid: valid)
            }
            for bad in [modified(virtual: true), modified(software: true), modified(valid: false),
                        modified(transport: "Virtual"), modified(usage: 6),
                        modified(classes: ["IOHIDPointingDevice", "IOHIDSystem", "IORegistryEntry"]),
                        modified(classes: ["IOHIDUserDevice", "IOHIDResourceDeviceUserClient", "IORegistryEntry"]),
                        modified(classes: Array(source.serviceClasses.prefix(2)))] {
                precondition(HIDPointerProfile.evaluate(bad, descriptor: descriptor) == nil)
            }
            precondition(HIDPointerProfile.evaluate(source, descriptor: descriptor + Data([0])) == nil)
        }
        let fifo: [UInt8] = [2, 0, 127, 129, 0, 0, 0, 0]
        let usb: [UInt8] = [1, 0, 0xff, 0x7f, 1, 0x80, 0]
        precondition(HIDPointerProfile.builtInRelative.decode(reportID: 2, bytes: fifo)?.dx == 127)
        precondition(HIDPointerProfile.builtInRelative.decode(reportID: 2, bytes: fifo)?.dy == -127)
        precondition(HIDPointerProfile.usbRelative.decode(reportID: 1, bytes: usb)?.dx == 32767)
        precondition(HIDPointerProfile.usbRelative.decode(reportID: 1, bytes: usb)?.dy == -32767)
        for (profile, packet, id) in [(HIDPointerProfile.builtInRelative, fifo, UInt32(2)), (.usbRelative, usb, 1)] {
            for length in 0..<packet.count {
                precondition(profile.decode(reportID: id, bytes: Array(packet.prefix(length))) == nil)
            }
            precondition(profile.decode(reportID: id, bytes: packet + [0]) == nil)
            precondition(profile.decode(reportID: 99, bytes: packet) == nil)
            for buttons in 2...255 {
                var altered = packet
                altered[1] = UInt8(buttons)
                precondition(profile.decode(reportID: id, bytes: altered) == nil)
            }
            var altered = packet
            altered[packet.count - 1] = 1
            precondition(profile.decode(reportID: id, bytes: altered) == nil)
        }
        func report(_ x: Int = 0, _ y: Int = 0, down: Bool = false) -> HIDPointerReport {
            HIDPointerReport(dx: x, dy: y, primaryDown: down)
        }
        var state = HardwarePointerState()
        state.arm(size: CGSize(width: 100, height: 100), now: 1)
        precondition(state.receive(report(down: true), time: 1.01, now: 1.01) == nil)
        precondition(state.receive(report(5, -5), time: 1.02, now: 1.02)?.position == CGPoint(x: 55, y: 45))
        precondition(state.receive(report(down: true), time: 1.03, now: 1.03)?.click == false)
        precondition(state.receive(report(), time: 1.04, now: 1.04)?.click == true)
        precondition(state.receive(report(), time: 1.05, now: 1.05)?.click == false)
        _ = state.receive(report(down: true), time: 1.06, now: 1.06)
        _ = state.receive(report(10, down: true), time: 1.07, now: 1.07)
        precondition(state.receive(report(), time: 1.08, now: 1.08)?.click == false, "Dragging must not become a click")
        precondition(state.receive(report(4096, -4096), time: 1.09, now: 1.09)?.position == CGPoint(x: 99, y: 1))
        for (time, now) in [(1.0, 1.1), (0.9, 1.1), (1.2, 1.1), (1.1, 1.3), (.nan, 1.1)] {
            state.arm(size: CGSize(width: 100, height: 100), now: 1)
            precondition(state.receive(report(), time: time, now: now) == nil)
            precondition(state.receive(report(), time: 1.4, now: 1.4) == nil, "Invalid timing must disarm")
        }
        state.arm(size: CGSize(width: 100, height: 100), now: 1)
        _ = state.receive(report(), time: 1.01, now: 1.01)
        _ = state.receive(report(down: true), time: 1.02, now: 1.02)
        state.cancel()
        state.arm(size: CGSize(width: 100, height: 100), now: 2)
        precondition(state.receive(report(), time: 2.01, now: 2.01)?.click == false, "Old presses cannot cross sessions")
        precondition(state.receive(report(4097), time: 2.02, now: 2.02) == nil)
        print("Hardware pointer policy: measured descriptors, software-source rejection, packet boundaries, signed axes, click pairing, timing, movement cancellation, and session invalidation passed. Fabricated inputs only.")
    }
}

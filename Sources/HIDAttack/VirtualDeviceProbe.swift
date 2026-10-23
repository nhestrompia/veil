import Foundation
import CoreHID
import IOKit.hid
import IOKit.hidsystem

@main
enum VirtualDeviceProbe {
    static func main() throws {
        // A standard boot-keyboard report descriptor. No input report is dispatched.
        let descriptor = Data([0x05, 0x01, 0x09, 0x06, 0xa1, 0x01, 0x05, 0x07,
            0x19, 0xe0, 0x29, 0xe7, 0x15, 0x00, 0x25, 0x01, 0x75, 0x01,
            0x95, 0x08, 0x81, 0x02, 0x95, 0x01, 0x75, 0x08, 0x81, 0x01,
            0x95, 0x06, 0x75, 0x08, 0x15, 0x00, 0x25, 0x65, 0x05, 0x07,
            0x19, 0x00, 0x29, 0x65, 0x81, 0x00, 0xc0])
        let properties: [String: Any] = [kIOHIDReportDescriptorKey: descriptor,
            kIOHIDVendorIDKey: 0xffff, kIOHIDProductIDKey: 1, kIOHIDProductKey: "AgentFreeBrowser Research Control"]
        let legacy = IOHIDUserDeviceCreateWithProperties(kCFAllocatorDefault, properties as CFDictionary, 0)
        let modern = HIDVirtualDevice(properties: .init(descriptor: descriptor, vendorID: 0xffff,
            productID: 1, product: "AgentFreeBrowser Research Control"))
        let result: [String: Any] = ["ioHIDUserDeviceCreated": legacy != nil,
            "coreHIDVirtualDeviceCreated": modern != nil, "inputReportsSent": 0,
            "scope": "Ad hoc signed same-user process without virtual-device entitlement. No activation or report dispatch."]
        let data = try JSONSerialization.data(withJSONObject: result, options: [.prettyPrinted, .sortedKeys])
        print(String(decoding: data, as: UTF8.self))
        withExtendedLifetime((legacy, modern)) {}
    }
}

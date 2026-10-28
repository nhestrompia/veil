import Foundation

@main
enum HIDSourcePolicyTests {
    static func main() {
        let measured = ["AppleHIDTransportHIDDevice", "AppleHIDTransportInterface",
                        "AppleHIDTransportProtocolSCMFIFO", "AppleHIDTransportDeviceFIFO",
                        "AppleDockChannelDevice", "AppleDockChannel", "IORegistryEntry"]
        func source(classes: [String] = measured, transport: String? = "FIFO", virtual: Bool? = nil,
                    software: Bool = false, valid: Bool = true, usage: Int? = 6) -> HIDSourceSnapshot {
            HIDSourceSnapshot(serviceClasses: classes, transport: transport, virtualDevice: virtual,
                              primaryUsagePage: 1, primaryUsage: usage, softwareAncestor: software,
                              observationValid: valid)
        }
        precondition(HIDSourcePolicy.evaluate(source()) == .measuredBuiltInKeyboard)
        precondition(HIDSourcePolicy.evaluate(source(virtual: true)) == .softwareSource)
        precondition(HIDSourcePolicy.evaluate(source(transport: "Virtual")) == .softwareSource)
        precondition(HIDSourcePolicy.evaluate(source(software: true)) == .softwareSource)
        precondition(HIDSourcePolicy.evaluate(source(classes: ["IOHIDKeyboardDevice", "IOHIDSystem"],
            transport: nil, software: true)) == .softwareSource)
        precondition(HIDSourcePolicy.evaluate(source(classes: ["IOHIDUserDevice", "IOHIDResourceDeviceUserClient"],
            transport: "FIFO", virtual: false, software: true)) == .softwareSource)
        precondition(HIDSourcePolicy.evaluate(source(classes: ["UnknownKeyboard", "IORegistryEntry"])) == .unsupportedTopology)
        precondition(HIDSourcePolicy.evaluate(source(classes: Array(measured.prefix(3)))) == .unsupportedTopology)
        precondition(HIDSourcePolicy.evaluate(source(transport: nil)) == .unsupportedTopology)
        precondition(HIDSourcePolicy.evaluate(source(usage: 2)) == .unsupportedTopology)
        precondition(HIDSourcePolicy.evaluate(source(valid: false)) == .unavailable)
        precondition(HIDSourcePolicy.evaluate(.observe(0)) == .unavailable)
        print("HID source policy: 12 cases passed")
    }
}

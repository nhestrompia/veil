import Foundation
import IOKit
import IOKit.hid
import IOKit.hidsystem

struct HIDSourceSnapshot {
    let serviceClasses: [String]
    let transport: String?
    let virtualDevice: Bool?
    let primaryUsagePage: Int?
    let primaryUsage: Int?
    let softwareAncestor: Bool
    let observationValid: Bool

    static func observe(_ service: io_registry_entry_t) -> Self {
        guard service != 0 else {
            return Self(serviceClasses: [], transport: nil, virtualDevice: nil,
                        primaryUsagePage: nil, primaryUsage: nil,
                        softwareAncestor: false, observationValid: false)
        }
        func property(_ key: String) -> CFTypeRef? {
            IORegistryEntryCreateCFProperty(service, key as CFString, kCFAllocatorDefault, 0)?.takeRetainedValue()
        }
        func soleParent(_ entry: io_registry_entry_t) -> (entry: io_registry_entry_t, valid: Bool) {
            var parents: io_iterator_t = 0
            guard IORegistryEntryGetParentIterator(entry, kIOServicePlane, &parents) == KERN_SUCCESS else { return (0, false) }
            defer { IOObjectRelease(parents) }
            let first = IOIteratorNext(parents)
            let second = IOIteratorNext(parents)
            guard second == 0, IOIteratorIsValid(parents) != 0 else {
                if first != 0 { IOObjectRelease(first) }
                if second != 0 { IOObjectRelease(second) }
                return (0, false)
            }
            return (first, true)
        }
        let transportValue = property(kIOHIDTransportKey)
        let virtualValue = property(kIOHIDVirtualHIDevice)
        let valid = (transportValue.map { CFGetTypeID($0) == CFStringGetTypeID() } ?? true)
            && (virtualValue.map { CFGetTypeID($0) == CFBooleanGetTypeID() } ?? true)
        var classes: [String] = []
        var software = false
        var reachedRoot = false
        var current = service
        IOObjectRetain(current)
        defer { if current != 0 { IOObjectRelease(current) } }
        for _ in 0..<24 {
            var name = [CChar](repeating: 0, count: 128)
            guard IOObjectGetClass(current, &name) == KERN_SUCCESS else { break }
            let className = String(decoding: name.prefix { $0 != 0 }.map { UInt8(bitPattern: $0) }, as: UTF8.self)
            classes.append(className)
            for kind in ["IOHIDUserDevice", "IOHIDResourceDeviceUserClient", "IOHIDSystem"] {
                if IOObjectConformsTo(current, kind) != 0 { software = true }
            }
            let parent = soleParent(current)
            guard parent.valid else { break }
            if parent.entry == 0 {
                reachedRoot = className == "IORegistryEntry"
                break
            }
            IOObjectRelease(current)
            current = parent.entry
        }
        return Self(serviceClasses: classes, transport: transportValue as? String,
                    virtualDevice: virtualValue as? Bool,
                    primaryUsagePage: property(kIOHIDPrimaryUsagePageKey) as? Int,
                    primaryUsage: property(kIOHIDPrimaryUsageKey) as? Int, softwareAncestor: software,
                    observationValid: valid && reachedRoot)
    }
}

enum HIDSourcePolicy {
    enum Decision: String {
        case measuredBuiltInKeyboard = "measured-built-in-keyboard"
        case softwareSource = "software-source"
        case unsupportedTopology = "unsupported-topology"
        case unavailable = "unavailable"
    }

    static func evaluate(_ source: HIDSourceSnapshot) -> Decision {
        guard source.observationValid else { return .unavailable }
        if source.softwareAncestor || source.virtualDevice == true || source.transport == "Virtual" {
            return .softwareSource
        }
        // This measured hardware profile is a research limit, not human attestation.
        let prefix = ["AppleHIDTransportHIDDevice", "AppleHIDTransportInterface",
                      "AppleHIDTransportProtocolSCMFIFO", "AppleHIDTransportDeviceFIFO",
                      "AppleDockChannelDevice", "AppleDockChannel"]
        guard source.primaryUsagePage == 1, source.primaryUsage == 6,
              source.transport == "FIFO", source.serviceClasses.starts(with: prefix) else {
            return .unsupportedTopology
        }
        return .measuredBuiltInKeyboard
    }
}

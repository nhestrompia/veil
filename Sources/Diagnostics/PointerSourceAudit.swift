import Foundation
import CryptoKit
import IOKit
import IOKit.hid

@main
enum PointerSourceAudit {
    static func main() throws {
        var iterator: io_iterator_t = 0
        let status = IOServiceGetMatchingServices(kIOMainPortDefault, IOServiceMatching("IOHIDDevice"), &iterator)
        guard status == KERN_SUCCESS else { throw NSError(domain: "PointerRegistryAudit", code: Int(status)) }
        defer { IOObjectRelease(iterator) }
        var rows: [[String: Any]] = []
        while true {
            let service = IOIteratorNext(iterator)
            if service == 0 { break }
            defer { IOObjectRelease(service) }
            let source = HIDSourceSnapshot.observe(service)
            guard source.primaryUsagePage == 1, source.primaryUsage == 1 || source.primaryUsage == 2 else { continue }
            let descriptor = IORegistryEntryCreateCFProperty(service, kIOHIDReportDescriptorKey as CFString,
                kCFAllocatorDefault, 0)?.takeRetainedValue() as? Data
            rows.append([
                "serviceClasses": source.serviceClasses, "transport": source.transport as Any? ?? NSNull(),
                "virtualDevice": source.virtualDevice as Any? ?? NSNull(), "softwareAncestor": source.softwareAncestor,
                "observationValid": source.observationValid,
                "primaryUsagePage": source.primaryUsagePage as Any? ?? NSNull(),
                "primaryUsage": source.primaryUsage as Any? ?? NSNull(),
                "reportDescriptor": descriptor?.map { String(format: "%02x", $0) }.joined() as Any? ?? NSNull(),
                "reportDescriptorSHA256": descriptor.map { SHA256.hash(data: $0).map { String(format: "%02x", $0) }.joined() } as Any? ?? NSNull()
            ])
        }
        let report: [String: Any] = ["devices": rows, "physicalInputVerified": false,
            "scope": "Read-only registry classes and report descriptors. No device open, value read, input collection, or identifiers."]
        let data = try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
        print(String(decoding: data, as: UTF8.self))
    }
}

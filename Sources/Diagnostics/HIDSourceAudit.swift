import Foundation
import IOKit
import IOKit.hid

@main
enum HIDSourceAudit {
    static func main() throws {
        var iterator: io_iterator_t = 0
        let status = IOServiceGetMatchingServices(kIOMainPortDefault, IOServiceMatching("IOHIDDevice"), &iterator)
        var rows: [[String: Any]] = []
        if status == KERN_SUCCESS {
            defer { IOObjectRelease(iterator) }
            while true {
                let service = IOIteratorNext(iterator)
                if service == 0 { break }
                defer { IOObjectRelease(service) }
                let source = HIDSourceSnapshot.observe(service)
                guard source.primaryUsagePage == 1 && source.primaryUsage == 6 || source.softwareAncestor else { continue }
                rows.append([
                    "serviceClasses": source.serviceClasses,
                    "transport": source.transport as Any? ?? NSNull(),
                    "virtualDevice": source.virtualDevice as Any? ?? NSNull(),
                    "primaryUsagePage": source.primaryUsagePage as Any? ?? NSNull(),
                    "primaryUsage": source.primaryUsage as Any? ?? NSNull(),
                    "softwareAncestor": source.softwareAncestor,
                    "observationValid": source.observationValid,
                    "decision": HIDSourcePolicy.evaluate(source).rawValue
                ])
            }
        }
        let report: [String: Any] = ["status": status, "devices": rows,
            "scope": "Read-only IORegistry classification. No device open, input collection, identifiers, or reports."]
        let data = try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
        print(String(decoding: data, as: UTF8.self))
    }
}

import Darwin
import Foundation
import ObjectiveC

// Read class metadata only. Do not instantiate a client or invoke its methods.
signal(SIGALRM, SIG_DFL)
alarm(5)
guard getuid() != 0, CommandLine.arguments.count == 1 else { exit(2) }

let image = "/System/Library/PrivateFrameworks/WebInspector.framework/Versions/A/WebInspector"
var report: [String: Any] = [
    "status": "metadata-only", "image": image,
    "system": ProcessInfo.processInfo.operatingSystemVersionString,
    "clientInstantiated": false, "clientMethodInvoked": false,
    "explicitRelayConnectionRequested": false, "browserQueried": false,
    "libraryInitializersAudited": false, "relayTrafficMonitored": false,
    "permissionRequested": false, "inputPosted": false,
]
if let library = dlopen(image, RTLD_LAZY | RTLD_LOCAL) {
    defer { dlclose(library) }
    report["libraryLoaded"] = true
    var count: UInt32 = 0
    if let names = objc_copyClassNamesForImage(image, &count) {
        defer { free(names) }
        let allowed: Set<String> = ["RWIApplication", "RWIBaseManager", "RWIChannel", "RWIDebuggable",
                                    "RWIInspector", "RWIMachine", "RWIManager", "RWIRelayDelegateMac",
                                    "RWIServiceXPCConnection", "RWITarget"]
        let selected = (0..<Int(count)).map { String(cString: names[$0]) }.filter { allowed.contains($0) }.sorted()
        report["classCount"] = count
        report["selectedClassCount"] = selected.count
        var classes: [[String: Any]] = []
        for name in selected {
            guard let type = NSClassFromString(name),
                  let owner = class_getImageName(type), String(cString: owner) == image else { continue }
            var methodCount: UInt32 = 0
            var selectors: [[String: String]] = []
            if let methods = class_copyMethodList(type, &methodCount) {
                defer { free(methods) }
                selectors = (0..<Int(methodCount)).map { index in
                    let method = methods[index]
                    return ["name": NSStringFromSelector(method_getName(method)),
                            "encoding": method_getTypeEncoding(method).map { String(cString: $0) } ?? "unavailable"]
                }.sorted { $0["name", default: ""] < $1["name", default: ""] }
            }
            classes.append(["class": name, "instanceMethodCount": methodCount,
                            "selectors": Array(selectors.prefix(96)), "methodLimitReached": selectors.count > 96])
        }
        report["classes"] = classes
    } else {
        report["classEnumerationAvailable"] = false
    }
} else {
    report["libraryLoaded"] = false
}
let data = try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
print(String(decoding: data, as: UTF8.self))

import Darwin
import Foundation
import ObjectiveC
import WebKit

// Inspect class metadata only. Do not create an inspector or contact its relay.
signal(SIGALRM, SIG_DFL)
alarm(5)
guard getuid() != 0 else { exit(2) }
let frameworkClass: AnyClass = WKWebView.self
let classes = [
    "WKWebView": ["isInspectable", "setInspectable:"],
    "_WKRemoteWebInspectorViewController": ["initWithConfiguration:",
                                            "loadForDebuggable:backendCommandsURL:",
                                            "sendMessageToFrontend:", "setDelegate:"],
    "_WKInspectorConfiguration": ["init"],
    "_WKInspectorDebuggableInfo": ["init"]
]
var observations: [String: Any] = [:]
for (name, selectors) in classes {
    guard let type = name == "WKWebView" ? frameworkClass : NSClassFromString(name) else {
        observations[name] = ["available": false]
        continue
    }
    var methods: [String: Any] = [:]
    for name in selectors {
        if let method = class_getInstanceMethod(type, NSSelectorFromString(name)),
           let encoding = method_getTypeEncoding(method) {
            methods[name] = ["available": true, "typeEncoding": String(cString: encoding)]
        } else {
            methods[name] = ["available": false]
        }
    }
    observations[name] = ["available": true, "methods": methods]
}
let report: [String: Any] = ["status": "metadata-only", "classes": observations,
                            "system": ProcessInfo.processInfo.operatingSystemVersionString,
                            "inspectorInstantiated": false, "relayContacted": false,
                            "permissionRequested": false, "inputPosted": false,
                            "browserQueried": false, "attachmentAttempted": false]
let data = try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
print(String(decoding: data, as: UTF8.self))

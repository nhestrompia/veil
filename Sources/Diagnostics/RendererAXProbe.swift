import AppKit
import ApplicationServices

@main
enum RendererAXProbe {
    @MainActor private static func query(_ scope: RendererProcessScope, renderer: ResearchProcessIdentity,
                                        expectedURL: URL?, tokenScan: Bool) throws -> [String: Any] {
        try scope.validate(renderer)
        let root = AXUIElementCreateApplication(renderer.pid)
        AXUIElementSetMessagingTimeout(root, 0.5)
        var pending: [(AXUIElement, Int)] = [(root, 0)]
        var visited: Set<AXUIElement> = []
        var roles: [String: Int] = [:]
        var markers: Set<String> = []
        var field: AXUIElement?
        var button: AXUIElement?
        var fixtureArea: AXUIElement?
        var discarded = 0
        let deadline = ProcessInfo.processInfo.systemUptime + 8

        func owned(_ element: AXUIElement) throws -> Bool {
            try scope.validate(renderer)
            var owner: pid_t = 0
            return AXUIElementGetPid(element, &owner) == .success && owner == renderer.pid
        }

        func attribute(_ element: AXUIElement, _ name: String) throws -> CFTypeRef? {
            guard try owned(element) else { return nil }
            AXUIElementSetMessagingTimeout(element, 0.25)
            var value: CFTypeRef?
            _ = AXUIElementCopyAttributeValue(element, name as CFString, &value)
            return value
        }

        let pattern = try NSRegularExpression(pattern: "AFB-[0-9A-F]{8}")
        var scanned = 0
        var tokenRoots = 0
        var tokenFactoryAvailable = false
        if tokenScan, let library = dlopen(nil, RTLD_LAZY | RTLD_LOCAL) {
            defer { dlclose(library) }
            if let symbol = dlsym(library, "_AXUIElementCreateWithRemoteToken") {
                typealias Factory = @convention(c) (CFData) -> Unmanaged<AXUIElement>?
                let create = unsafeBitCast(symbol, to: Factory.self)
                tokenFactoryAvailable = true
                let scanDeadline = min(deadline, ProcessInfo.processInfo.systemUptime + 3)
                for id in UInt64(0)..<1024 {
                    if ProcessInfo.processInfo.systemUptime >= scanDeadline { break }
                    try scope.validate(renderer)
                    guard let data = RendererRemoteToken.data(pid: renderer.pid, elementID: id) else { break }
                    scanned += 1
                    guard let element = create(data as CFData)?.takeRetainedValue(), try owned(element) else { continue }
                    if try attribute(element, kAXRoleAttribute) as? String != nil {
                        pending.append((element, 0))
                        tokenRoots += 1
                    }
                }
            }
        }
        while let (element, depth) = pending.popLast(), visited.count < 500,
              ProcessInfo.processInfo.systemUptime < deadline {
            guard visited.insert(element).inserted else { continue }
            guard try owned(element) else { discarded += 1; continue }
            let role = try attribute(element, kAXRoleAttribute) as? String ?? "unavailable"
            roles[role, default: 0] += 1
            if role == kAXMenuBarRole { continue }
            if role == "AXWebArea", let expectedURL,
               let url = try attribute(element, kAXURLAttribute) as? URL, url == expectedURL {
                fixtureArea = element
            }
            var labels: [String] = []
            for key in [kAXTitleAttribute, kAXDescriptionAttribute, kAXValueAttribute] {
                guard let text = try attribute(element, key) as? String else { continue }
                labels.append(text)
                let range = NSRange(text.startIndex..., in: text)
                for match in pattern.matches(in: text, range: range) {
                    if let range = Range(match.range, in: text) { markers.insert(String(text[range])) }
                }
            }
            if role == kAXTextFieldRole && labels.contains("Enter native-input") { field = element }
            if role == kAXButtonRole && labels.contains("Record action") { button = element }
            if depth < 25 {
                for key in [kAXChildrenAttribute, kAXWindowsAttribute] {
                    if let children = try attribute(element, key) as? [AXUIElement] {
                        pending.append(contentsOf: children.reversed().prefix(500).map { ($0, depth + 1) })
                    }
                }
            }
        }
        var result: [String: Any] = ["rendererPID": renderer.pid, "visitedCount": visited.count,
                                    "roles": roles, "discardedUnownedElements": discarded,
                                    "researchMarkers": markers.sorted(), "fieldAvailable": field != nil,
                                    "buttonAvailable": button != nil, "fixtureURLVerified": fixtureArea != nil,
                                    "actionAttempted": false,
                                    "rawTextSaved": false, "tokenScanRequested": tokenScan,
                                    "tokenFactoryAvailable": tokenFactoryAvailable,
                                    "scannedElementIDs": scanned, "resolvableTokenRoots": tokenRoots,
                                    "traversalIncomplete": !pending.isEmpty]
        if let expectedURL, let fixtureArea,
           let currentURL = try attribute(fixtureArea, kAXURLAttribute) as? URL, currentURL == expectedURL,
           let field, let button, try owned(field), try owned(button),
           NSWorkspace.shared.frontmostApplication?.processIdentifier == scope.host.pid {
            let value = AXUIElementSetAttributeValue(field, kAXValueAttribute as CFString, "native-input" as CFString)
            try scope.validate(renderer)
            result["setValueError"] = value.rawValue
            if value == .success {
                result["pressError"] = AXUIElementPerformAction(button, kAXPressAction as CFString).rawValue
                result["actionAttempted"] = true
            }
        }
        return result
    }

    @MainActor static func main() {
        let args = Array(CommandLine.arguments.dropFirst())
        var result: [String: Any] = ["accessibility": AXIsProcessTrusted(), "permissionRequested": false,
                                    "inputTapInstalled": false]
        do {
            guard args == ["permissions"] || args.count == 2 && ["discover", "read", "read-token"].contains(args[0])
                    || args.count == 3 && ["action", "action-token"].contains(args[0]) else {
                throw RendererScopeError.unrelatedHost
            }
            if args[0] != "permissions" {
                guard let pid = pid_t(args[1]) else { throw RendererScopeError.unrelatedHost }
                let scope = try RendererProcessScope(hostPID: pid)
                var expectedURL: URL?
                if args[0].hasPrefix("action") {
                    guard let url = RendererFixtureURL.parse(args[2]) else {
                        throw RendererScopeError.unrelatedHost
                    }
                    expectedURL = url
                }
                let renderers = try scope.renderers()
                result["hostPID"] = pid
                result["renderers"] = renderers.map { ["pid": $0.pid, "path": $0.path] as [String: Any] }
                result["ownershipMethod"] = "Exact research executable, process start time, OS responsibility PID. Private metadata API."
                result["accessibilityQueried"] = false
                if args[0] != "discover" {
                    guard AXIsProcessTrusted() else {
                        result["status"] = "inconclusive"
                        result["reason"] = "This helper has no effective Accessibility grant. No AX query or action ran."
                        return write(result)
                    }
                    if args[0].hasPrefix("action") {
                        NSRunningApplication(processIdentifier: pid)?.activate(options: [])
                        Thread.sleep(forTimeInterval: 0.3)
                    }
                    result["queries"] = try renderers.map {
                        try query(scope, renderer: $0, expectedURL: expectedURL, tokenScan: args[0].hasSuffix("-token"))
                    }
                    result["accessibilityQueried"] = !renderers.isEmpty
                }
            }
            result["status"] = "observed"
        } catch {
            result["status"] = "refused"
            result["error"] = String(describing: error)
        }
        write(result)
    }

    private static func write(_ result: [String: Any]) {
        if let data = try? JSONSerialization.data(withJSONObject: result, options: [.prettyPrinted, .sortedKeys]) {
            print(String(decoding: data, as: UTF8.self))
        }
    }
}

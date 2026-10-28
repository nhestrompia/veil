import AppKit
@preconcurrency import ApplicationServices
import Darwin

@main
enum PreviewRendererReadProbe {
    @MainActor static func query(_ identity: ResearchProcessIdentity, scope: PreviewAXScope,
                                 tokens: Bool, deadline: Double) throws -> [String: Any] {
        try scope.validate(identity)
        let root = AXUIElementCreateApplication(identity.pid)
        var pending = [(root, 0)]
        var visited: Set<AXUIElement> = []
        var roles: [String: Int] = [:]
        var markers: Set<String> = []
        var discarded = 0
        var scanned = 0
        var tokenRoots = 0
        var tokenFactoryAvailable = false

        func validate(_ element: AXUIElement) throws -> Bool {
            try scope.validate(identity)
            guard NSWorkspace.shared.frontmostApplication?.processIdentifier == scope.host.pid else {
                throw RendererScopeError.changedIdentity
            }
            var owner: pid_t = 0
            return AXUIElementGetPid(element, &owner) == .success && owner == identity.pid
        }

        func attribute(_ element: AXUIElement, _ name: String) throws -> CFTypeRef? {
            guard try validate(element), ProcessInfo.processInfo.systemUptime < deadline else { return nil }
            AXUIElementSetMessagingTimeout(element, 0.1)
            var result: CFTypeRef?
            _ = AXUIElementCopyAttributeValue(element, name as CFString, &result)
            return result
        }

        if tokens, let library = dlopen(nil, RTLD_LAZY | RTLD_LOCAL) {
            defer { dlclose(library) }
            if let symbol = dlsym(library, "_AXUIElementCreateWithRemoteToken") {
                typealias Factory = @convention(c) (CFData) -> Unmanaged<AXUIElement>?
                let create = unsafeBitCast(symbol, to: Factory.self)
                tokenFactoryAvailable = true
                let scanDeadline = min(deadline, ProcessInfo.processInfo.systemUptime + 2)
                for identifier in UInt64(0)..<1024 {
                    guard ProcessInfo.processInfo.systemUptime < scanDeadline else { break }
                    try scope.validate(identity)
                    guard let data = RendererRemoteToken.data(pid: identity.pid, elementID: identifier) else { break }
                    scanned += 1
                    guard let element = create(data as CFData)?.takeRetainedValue(), try validate(element),
                          try attribute(element, kAXRoleAttribute) as? String != nil else { continue }
                    pending.append((element, 0))
                    tokenRoots += 1
                }
            }
        }
        while let (element, depth) = pending.popLast(), visited.count < 500,
              ProcessInfo.processInfo.systemUptime < deadline {
            guard visited.insert(element).inserted else { continue }
            guard try validate(element) else { discarded += 1; continue }
            let role = try attribute(element, kAXRoleAttribute) as? String ?? "unavailable"
            roles[role, default: 0] += 1
            if role == kAXMenuBarRole { continue }
            for key in [kAXTitleAttribute, kAXDescriptionAttribute, kAXValueAttribute] {
                if let text = try attribute(element, key) as? String {
                    markers.formUnion(PreviewAXHostPolicy.markers(in: text))
                }
            }
            if depth < 25 {
                for key in [kAXChildrenAttribute, kAXWindowsAttribute] {
                    if let children = try attribute(element, key) as? [AXUIElement] {
                        pending.append(contentsOf: children.prefix(500).map { ($0, depth + 1) })
                    }
                }
            }
        }
        return ["pid": identity.pid, "kind": identity == scope.host ? "host" : "renderer",
                "visited": visited.count, "roles": roles, "researchMarkers": markers.sorted(),
                "discardedForeignElements": discarded, "scannedElementIDs": scanned,
                "tokenFactoryAvailable": tokenFactoryAvailable, "resolvableTokenRoots": tokenRoots,
                "traversalIncomplete": !pending.isEmpty || visited.count >= 500
                    || ProcessInfo.processInfo.systemUptime >= deadline]
    }

    @MainActor static func main() {
        signal(SIGALRM, SIG_DFL)
        alarm(20)
        _ = NSApplication.shared
        NSApp.setActivationPolicy(.prohibited)
        var report: [String: Any] = ["status": "refused", "accessibility": AXIsProcessTrusted(),
                                     "permissionRequested": false, "accessibilityQueried": false,
                                     "actionsSent": false, "inputPosted": false, "hooksInstalled": false,
                                     "rawTextSaved": false, "probePID": getpid()]
        var output: URL?
        do {
            let arguments = Array(CommandLine.arguments.dropFirst())
            guard getuid() != 0, arguments.count >= 3,
                  arguments[arguments.count - 2] == "--out" else { throw RendererScopeError.unrelatedHost }
            let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
            let destination = URL(fileURLWithPath: arguments.last!).standardizedFileURL
            guard destination.resolvingSymlinksInPath().path.hasPrefix(root.appendingPathComponent("artifacts").resolvingSymlinksInPath().path + "/"),
                  destination.pathExtension == "json", !FileManager.default.fileExists(atPath: destination.path) else {
                throw RendererScopeError.unrelatedHost
            }
            output = destination
            let command = Array(arguments.dropLast(2))
            if command == ["permissions"] {
                report["status"] = "preflight"
            } else if command == ["request-accessibility"] {
                report["permissionRequested"] = true
                report["status"] = "requested"
                report["accessibility"] = AXIsProcessTrustedWithOptions(
                    [kAXTrustedCheckOptionPrompt.takeUnretainedValue() as String: true] as CFDictionary)
            } else {
                guard command.count == 2, ["discover", "read", "read-token"].contains(command[0]),
                      let pid = Int32(command[1]) else { throw RendererScopeError.unrelatedHost }
                let scope = try PreviewAXScope(pid: pid, root: root)
                let renderers = try scope.renderers()
                report["hostPID"] = pid
                report["hostName"] = scope.policy.name
                report["hostSHA256"] = scope.policy.digest
                report["rendererPIDs"] = renderers.map(\.pid)
                report["status"] = "discovered"
                if command[0] != "discover" {
                    guard AXIsProcessTrusted() else {
                        report["status"] = "inconclusive"
                        report["reason"] = "This helper has no Accessibility grant. No AX query ran."
                        return write(report, to: output)
                    }
                    guard NSWorkspace.shared.frontmostApplication?.processIdentifier == pid else {
                        throw RendererScopeError.changedIdentity
                    }
                    let deadline = ProcessInfo.processInfo.systemUptime + 12
                    report["accessibilityQueried"] = true
                    report["queries"] = try (renderers + [scope.host]).map {
                        try query($0, scope: scope, tokens: command[0] == "read-token", deadline: deadline)
                    }
                    try scope.verifyImage()
                    report["status"] = "observed"
                }
            }
        } catch {
            report["error"] = String(describing: error)
        }
        write(report, to: output)
    }

    private static func write(_ report: [String: Any], to output: URL?) {
        guard let data = try? JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys]) else { return }
        if let output { try? data.write(to: output, options: .atomic) }
        print(String(decoding: data, as: UTF8.self))
    }
}

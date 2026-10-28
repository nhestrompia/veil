import AppKit
import Darwin
import ObjectiveC

private enum DiscoveryError: Error {
    case invalidFixture, unavailableInterface, unexpectedMetadata
}

@MainActor
private enum InspectorObjects {
    private static func method(_ object: AnyObject, _ name: String, encoding: String) throws -> (Selector, IMP) {
        let selector = NSSelectorFromString(name)
        guard let type = object_getClass(object), let method = class_getInstanceMethod(type, selector),
              let raw = method_getTypeEncoding(method), String(cString: raw) == encoding else {
            throw DiscoveryError.unavailableInterface
        }
        return (selector, method_getImplementation(method))
    }

    static func manager() throws -> AnyObject {
        guard let type = NSClassFromString("RWIManager"),
              let method = class_getClassMethod(type, NSSelectorFromString("sharedManager")),
              let encoding = method_getTypeEncoding(method), String(cString: encoding) == "@16@0:8" else {
            throw DiscoveryError.unavailableInterface
        }
        typealias Create = @convention(c) (AnyClass, Selector) -> Unmanaged<AnyObject>?
        let create = unsafeBitCast(method_getImplementation(method), to: Create.self)
        guard let manager = create(type, NSSelectorFromString("sharedManager"))?.takeUnretainedValue() else {
            throw DiscoveryError.unavailableInterface
        }
        return manager
    }

    static func localTarget(_ manager: AnyObject, create: Bool) throws {
        let name = create ? "_createCurrentMachineTarget" : "_removeCurrentMachineTarget"
        let (selector, implementation) = try method(manager, name, encoding: "v16@0:8")
        typealias Operation = @convention(c) (AnyObject, Selector) -> Void
        unsafeBitCast(implementation, to: Operation.self)(manager, selector)
    }

    static func get(_ object: AnyObject, _ name: String) throws -> AnyObject? {
        let (selector, implementation) = try method(object, name, encoding: "@16@0:8")
        typealias Get = @convention(c) (AnyObject, Selector) -> Unmanaged<AnyObject>?
        return unsafeBitCast(implementation, to: Get.self)(object, selector)?.takeUnretainedValue()
    }

    static func application(_ machine: AnyObject, identifier: String) throws -> AnyObject? {
        let (selector, implementation) = try method(machine, "applicationWithIdentifier:", encoding: "@24@0:8@16")
        typealias Get = @convention(c) (AnyObject, Selector, NSString) -> Unmanaged<AnyObject>?
        return unsafeBitCast(implementation, to: Get.self)(machine, selector, identifier as NSString)?.takeUnretainedValue()
    }
}

@main
private enum InspectorDiscoveryControl {
    @MainActor static func main() {
        signal(SIGALRM, SIG_DFL)
        alarm(15)
        var report: [String: Any] = ["status": "inconclusive", "referenceOnly": true,
                                     "managerInstantiated": false,
                                     "channelOpened": false, "scriptSent": false, "inputPosted": false,
                                     "permissionRequested": false, "unrelatedPageMetadataSaved": false]
        do {
            let args = CommandLine.arguments
            guard args.count == 3, let pid = Int32(args[1]), let fixture = URL(string: args[2]),
                  args[2].count <= 512, fixture.scheme == "http", fixture.host == "127.0.0.1",
                  let port = fixture.port, (1...65535).contains(port), fixture.user == nil, fixture.password == nil,
                  fixture.query == nil, fixture.fragment == nil,
                  fixture.path.range(of: #"^/trial/[a-f0-9]{16}$"#, options: .regularExpression) != nil else {
                throw DiscoveryError.invalidFixture
            }
            let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
            let scope = try PreviewAXScope(pid: pid, root: root)
            guard scope.policy.name == "InspectableControl" else { throw RendererScopeError.unrelatedHost }
            let identities = [scope.host] + (try scope.renderers())
            let image = "/System/Library/PrivateFrameworks/WebInspector.framework/Versions/A/WebInspector"
            guard let library = dlopen(image, RTLD_LAZY | RTLD_LOCAL) else { throw DiscoveryError.unavailableInterface }
            defer { dlclose(library) }
            let manager = try InspectorObjects.manager()
            report["managerInstantiated"] = true
            report["managerFactory"] = "sharedManager"
            try InspectorObjects.localTarget(manager, create: true)
            report["localTargetCreationRequested"] = true
            defer {
                do {
                    try InspectorObjects.localTarget(manager, create: false)
                    report["localTargetRemovalRequested"] = true
                } catch {
                    report["localTargetRemovalRequested"] = false
                }
            }
            let deadline = ProcessInfo.processInfo.systemUptime + 8
            var sawMachine = false
            var seenApplications: Set<pid_t> = []
            var matchedPages: Set<String> = []
            repeat {
                try scope.verifyImage()
                for identity in identities { try scope.validate(identity) }
                if let machine = try InspectorObjects.get(manager, "currentMachine") {
                    sawMachine = true
                    for identity in identities {
                        let identifier = "PID:\(identity.pid)"
                        guard let app = try InspectorObjects.application(machine, identifier: identifier) else { continue }
                        guard try InspectorObjects.get(app, "identifier") as? String == identifier else {
                            throw DiscoveryError.unexpectedMetadata
                        }
                        seenApplications.insert(identity.pid)
                        guard let pages = try InspectorObjects.get(app, "allDebuggables") as? [AnyObject], pages.count <= 4 else {
                            throw DiscoveryError.unexpectedMetadata
                        }
                        for page in pages {
                            guard try InspectorObjects.get(page, "url") as? String == fixture.absoluteString else { continue }
                            guard let pageID = try InspectorObjects.get(page, "pageId") as? NSNumber else {
                                throw DiscoveryError.unexpectedMetadata
                            }
                            matchedPages.insert("\(identity.pid):\(pageID.uint64Value)")
                        }
                    }
                }
                if matchedPages.count == 1 { break }
                RunLoop.current.run(until: Date().addingTimeInterval(0.05))
            } while ProcessInfo.processInfo.systemUptime < deadline
            try scope.verifyImage()
            report["status"] = matchedPages.count == 1 ? "reference-discovered" : "inconclusive"
            report["currentMachineSeen"] = sawMachine
            report["ownedApplicationsSeen"] = seenApplications.count
            report["matchingFixturePages"] = matchedPages.count
            report["targetPID"] = pid
            report["targetSHA256"] = scope.policy.digest
            report["discoveryMaximumSeconds"] = 8
        } catch {
            report["error"] = String(describing: error)
        }
        if let data = try? JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys]) {
            print(String(decoding: data, as: UTF8.self))
        }
    }
}

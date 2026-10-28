import AppKit
import CryptoKit
import Darwin

private struct LifecycleFailure: Error {
    let message: String
}

@main
private enum PreviewLifecycleProbe {
    @MainActor static func main() {
        alarm(5)
        _ = NSApplication.shared
        NSApp.setActivationPolicy(.prohibited)
        var report: [String: Any] = ["status": "refused", "inputPosted": false,
                                     "hooksInstalled": false, "permissionRequested": false]
        do {
            let args = Array(CommandLine.arguments.dropFirst())
            guard getuid() != 0, args.count == 2,
                  ["activate", "hide", "unhide"].contains(args[0]),
                  let pid = Int32(args[1]), pid > 1,
                  let app = NSRunningApplication(processIdentifier: pid),
                  let launched = app.launchDate, !app.isTerminated else {
                throw LifecycleFailure(message: "Use activate, hide, or unhide with an owned research PID")
            }
            let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
                .deletingLastPathComponent().deletingLastPathComponent()
            let pins = [
                ("AgentFreeBrowserPreview", "research.agentfreebrowser.preview",
                 "dc3ca62c174d635b9994d9bae27ff6d4dc4a7983bc36d332f720fbbfaf24df70"),
                ("InspectableControl", "research.agentfreebrowser.control",
                 "ac6b5b199ebfeafbeb53b85ad759c966bbd4f9b852cfc39ecd89af6b725bab36")
            ]
            guard let pin = pins.first(where: { $0.1 == app.bundleIdentifier }) else {
                throw LifecycleFailure(message: "The target is not an allowed research app")
            }
            let binary = root.appendingPathComponent("dist/\(pin.0).app/Contents/MacOS/\(pin.0)")
                .resolvingSymlinksInPath()
            guard app.executableURL?.resolvingSymlinksInPath() == binary else {
                throw LifecycleFailure(message: "The executable path changed")
            }
            let digest = SHA256.hash(data: try Data(contentsOf: binary)).map { String(format: "%02x", $0) }.joined()
            guard digest == pin.2 else { throw LifecycleFailure(message: "The executable hash changed") }
            let succeeded: Bool
            switch args[0] {
            case "hide": succeeded = app.hide()
            case "unhide": succeeded = app.unhide()
            default: succeeded = app.activate(options: [])
            }
            RunLoop.current.run(until: Date().addingTimeInterval(0.3))
            guard let after = NSRunningApplication(processIdentifier: pid), !after.isTerminated,
                  after.launchDate == launched, after.executableURL?.resolvingSymlinksInPath() == binary else {
                throw LifecycleFailure(message: "The process identity changed")
            }
            report.merge(["status": "observed", "pid": pid, "target": pin.0,
                          "binarySHA256": digest, "operation": args[0], "operationSucceeded": succeeded,
                          "targetActive": after.isActive, "targetHidden": after.isHidden],
                         uniquingKeysWith: { _, new in new })
        } catch {
            report["error"] = String(describing: error)
        }
        if let data = try? JSONSerialization.data(withJSONObject: report, options: [.sortedKeys]) {
            FileHandle.standardOutput.write(data)
            FileHandle.standardOutput.write(Data([10]))
        }
        alarm(0)
        if report["status"] as? String != "observed" { exit(2) }
    }
}

import AppKit
import CryptoKit
import Darwin

@main
private enum FocusEngineActivation {
    private static func startIdentity(_ pid: Int32) -> String? {
        var info = proc_bsdinfo()
        let size = MemoryLayout<proc_bsdinfo>.stride
        let received = withUnsafeMutablePointer(to: &info) {
            proc_pidinfo(pid, PROC_PIDTBSDINFO, 0, $0, Int32(size))
        }
        guard received == size else { return nil }
        return "\(info.pbi_start_tvsec):\(info.pbi_start_tvusec)"
    }

    @MainActor static func main() {
        alarm(5)
        _ = NSApplication.shared
        NSApp.setActivationPolicy(.prohibited)
        var result: [String: Any] = ["status": "refused", "inputPosted": false, "hooksInstalled": false]
        let args = Array(CommandLine.arguments.dropFirst())
        if getuid() != 0, geteuid() != 0, args.count == 2,
           ["activate", "hide", "unhide"].contains(args[0]), let pid = Int32(args[1]), pid > 1,
           let app = NSRunningApplication(processIdentifier: pid), let launched = startIdentity(pid),
           let pin = FocusActivationPins.targets.first(where: { $0.0 == app.bundleIdentifier }),
           app.executableURL?.resolvingSymlinksInPath().path == pin.1,
           let data = try? Data(contentsOf: URL(fileURLWithPath: pin.1)),
           SHA256.hash(data: data).map({ String(format: "%02x", $0) }).joined() == pin.2 {
            let succeeded: Bool
            switch args[0] {
            case "hide": succeeded = app.hide()
            case "unhide": succeeded = app.unhide()
            default: succeeded = app.activate(options: [])
            }
            RunLoop.current.run(until: Date().addingTimeInterval(0.3))
            result["operationAttempted"] = true
            if let after = NSRunningApplication(processIdentifier: pid) {
                result["targetTerminated"] = after.isTerminated
                result["startIdentityStable"] = startIdentity(pid) == launched
                result["executableURLStable"] = after.executableURL == app.executableURL
                if !after.isTerminated, startIdentity(pid) == launched, after.executableURL == app.executableURL {
                result.merge(["status": "observed", "pid": pid, "operation": args[0],
                              "operationSucceeded": succeeded, "active": after.isActive,
                              "hidden": after.isHidden, "binarySHA256": pin.2], uniquingKeysWith: { _, new in new })
                }
            }
        }
        if let data = try? JSONSerialization.data(withJSONObject: result, options: .sortedKeys) {
            FileHandle.standardOutput.write(data)
            FileHandle.standardOutput.write(Data([10]))
        }
        alarm(0)
        if result["status"] as? String != "observed" { exit(2) }
    }
}

import AppKit
import CryptoKit
import Darwin

@main
enum PreviewCaptureFocusTrace {
    @MainActor static func main() {
        signal(SIGALRM, SIG_DFL)
        alarm(20)
        var report: [String: Any] = ["status": "refused", "inputPosted": false, "activationRequested": false,
                                     "uiContentRead": false, "permissionRequested": false]
        do {
            guard getuid() != 0, CommandLine.arguments.count == 2,
                  let pid = Int32(CommandLine.arguments[1]) else { throw RendererScopeError.unrelatedHost }
            let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
            let scope = try PreviewAXScope(pid: pid, root: root)
            let manifest = try JSONSerialization.jsonObject(with: Data(contentsOf: root.appendingPathComponent("docs/evidence/preview-stream-permission-manifest.json"))) as? [String: Any]
            guard let expected = manifest?["executableSHA256"] as? String else { throw RendererScopeError.unrelatedHost }
            let path = root.appendingPathComponent("dist/PreviewStreamCaptureProbe.app/Contents/MacOS/PreviewStreamCaptureProbe")
            let digest = SHA256.hash(data: try Data(contentsOf: path)).map { String(format: "%02x", $0) }.joined()
            guard digest == expected else { throw RendererScopeError.changedIdentity }
            let start = ProcessInfo.processInfo.systemUptime
            var events: [[String: Any]] = []
            var previous = ""
            var sawProbe = false
            var probeIdentity: ResearchProcessIdentity?
            while ProcessInfo.processInfo.systemUptime - start < 12 {
                try scope.validate(scope.host)
                let apps = NSRunningApplication.runningApplications(withBundleIdentifier: "research.agentfreebrowser.previewstreamcapture").filter { !$0.isTerminated }
                guard apps.count <= 1 else { throw RendererScopeError.changedIdentity }
                if let app = apps.first {
                    guard let identity = try? ResearchProcessIdentity(pid: app.processIdentifier) else {
                        if sawProbe { break }
                        RunLoop.current.run(until: Date().addingTimeInterval(0.01))
                        continue
                    }
                    guard identity.path == path.path else { throw RendererScopeError.unrelatedHost }
                    if let probeIdentity, probeIdentity != identity { throw RendererScopeError.changedIdentity }
                    probeIdentity = identity
                    sawProbe = true
                }
                let front = NSWorkspace.shared.frontmostApplication
                let role: String
                if front?.processIdentifier == pid { role = "research-target" }
                else if front?.processIdentifier == probeIdentity?.pid { role = "capture-helper" }
                else if front?.bundleIdentifier == "com.t3tools.t3code" { role = "task-app" }
                else if front?.bundleIdentifier?.hasPrefix("com.apple.") == true { role = "apple-system-app" }
                else { role = "other" }
                if role != previous {
                    events.append(["seconds": ProcessInfo.processInfo.systemUptime - start,
                                   "foregroundRole": role, "captureHelperSeen": sawProbe])
                    report["events"] = events
                    previous = role
                }
                if sawProbe && apps.isEmpty { break }
                RunLoop.current.run(until: Date().addingTimeInterval(0.01))
            }
            report["status"] = "observed"
            report["targetPID"] = pid
            report["captureHelperSeen"] = sawProbe
            report["events"] = events
        } catch {
            report["error"] = String(describing: error)
        }
        if let data = try? JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys]) {
            print(String(decoding: data, as: UTF8.self))
        }
    }
}

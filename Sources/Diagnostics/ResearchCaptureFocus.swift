import AppKit
import CryptoKit
import Darwin

private struct FocusFailure: Error, CustomStringConvertible {
    let description: String
    init(_ value: String) { description = value }
}

@main
private enum ResearchCaptureFocus {
    @MainActor static func main() async {
        signal(SIGALRM, SIG_DFL)
        alarm(15)
        _ = NSApplication.shared
        NSApp.setActivationPolicy(.prohibited)
        var destination: URL?
        var events: [[String: Any]] = []
        var report: [String: Any] = ["status": "refused", "inputPosted": false, "hooksInstalled": false,
                                     "maximumActivations": 3, "maximumActiveSeconds": 8]
        do {
            let args = Array(CommandLine.arguments.dropFirst())
            guard [4, 5].contains(args.count), let targetPID = Int32(args[0]), targetPID > 1,
                  args.count == 4 || args[4] == "capture-stress" else {
                throw FocusFailure("Use TARGET_PID TARGET_SHA256 PROBE_SHA256 NEW_ARTIFACT.json [capture-stress]")
            }
            let stress = args.count == 5
            if stress { alarm(50) }
            let probeName = stress ? "CaptureStressProbe" : "CompositorRefreshProbe"
            let probeBundle = stress ? "research.agentfreebrowser.capturestress" : "research.agentfreebrowser.compositorrefresh"
            let activeSeconds: Double = stress ? 40 : 8
            report["maximumActiveSeconds"] = activeSeconds
            let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
            let output = URL(fileURLWithPath: args[3]).standardizedFileURL
            guard output.resolvingSymlinksInPath().path.hasPrefix(root.appendingPathComponent("artifacts").resolvingSymlinksInPath().path + "/"),
                  output.pathExtension == "json", !FileManager.default.fileExists(atPath: output.path) else {
                throw FocusFailure("Use a new JSON report within project artifacts")
            }
            destination = output
            let targetPath = root.appendingPathComponent("dist/InternalKeyboardControl.app/Contents/MacOS/InternalKeyboardControl")
            let probePath = root.appendingPathComponent("dist/\(probeName).app/Contents/MacOS/\(probeName)")
            func matches(_ app: NSRunningApplication, path: URL, bundle: String, digest: String) throws -> Bool {
                guard !app.isTerminated, app.bundleIdentifier == bundle,
                      app.executableURL?.resolvingSymlinksInPath() == path.resolvingSymlinksInPath() else { return false }
                return SHA256.hash(data: try Data(contentsOf: path)).map { String(format: "%02x", $0) }.joined() == digest
            }
            guard let target = NSRunningApplication(processIdentifier: targetPID),
                  try matches(target, path: targetPath, bundle: "research.agentfreebrowser.internalkeyboardcontrol", digest: args[1]),
                  let targetLaunch = target.launchDate else { throw FocusFailure("Target identity is not the owned research executable") }
            let waitStart = ProcessInfo.processInfo.systemUptime
            var probe: NSRunningApplication?
            while ProcessInfo.processInfo.systemUptime - waitStart < 5 {
                let candidates = NSWorkspace.shared.runningApplications.filter { $0.bundleIdentifier == probeBundle }
                if candidates.count == 1 { probe = candidates[0]; break }
                try await Task.sleep(for: .milliseconds(10))
            }
            guard let probe, try matches(probe, path: probePath, bundle: probeBundle, digest: args[2]),
                  let probeLaunch = probe.launchDate else { throw FocusFailure("A unique verified capture helper did not appear") }
            let start = ProcessInfo.processInfo.systemUptime
            var activations = 0
            var lastActivation = -1.0
            var previousRole = ""
            report["targetPID"] = targetPID
            report["probePID"] = probe.processIdentifier
            report["status"] = "observed"
            while ProcessInfo.processInfo.systemUptime - start < activeSeconds && !probe.isTerminated {
                guard !target.isTerminated, target.launchDate == targetLaunch, probe.launchDate == probeLaunch else {
                    throw FocusFailure("A measured process identity changed")
                }
                let front = NSWorkspace.shared.frontmostApplication
                let elapsed = ProcessInfo.processInfo.systemUptime - start
                let isTarget = front?.processIdentifier == targetPID
                let role = isTarget ? "research-target" : front?.processIdentifier == probe.processIdentifier ? "capture-helper" : "other"
                if role != previousRole {
                    events.append(["seconds": elapsed, "foregroundRole": role])
                    previousRole = role
                }
                if !isTarget && elapsed - lastActivation >= 0.25 {
                    if ["com.apple.UserNotificationCenter", "com.apple.systempreferences", "com.apple.SecurityAgent", "com.apple.loginwindow"].contains(front?.bundleIdentifier ?? "") {
                        report["status"] = "system-dialog-focus"
                        break
                    }
                    guard activations < 3 else { report["status"] = "activation-limit"; break }
                    guard try matches(target, path: targetPath, bundle: "research.agentfreebrowser.internalkeyboardcontrol", digest: args[1]),
                          try matches(probe, path: probePath, bundle: probeBundle, digest: args[2]) else {
                        throw FocusFailure("A measured executable changed")
                    }
                    let accepted = target.activate(options: [])
                    activations += 1
                    lastActivation = elapsed
                    events.append(["seconds": elapsed, "targetActivationAccepted": accepted])
                }
                try await Task.sleep(for: .milliseconds(10))
            }
            report["activations"] = activations
        } catch { report["error"] = String(describing: error) }
        report["events"] = events
        do {
            let data = try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
            if let destination { try data.write(to: destination, options: [.withoutOverwriting]) }
            print(String(decoding: data, as: UTF8.self))
        } catch { fputs("Cannot save focus coordination report\n", stderr) }
    }
}

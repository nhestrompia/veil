import AppKit
import CryptoKit

@main
private enum OwnedWindowMetadata {
    @MainActor static func main() {
        do { try observe() }
        catch {
            let report = ["status": "refused", "error": String(describing: error)]
            if let data = try? JSONSerialization.data(withJSONObject: report, options: [.sortedKeys]) {
                print(String(decoding: data, as: UTF8.self))
            }
            exit(2)
        }
    }

    @MainActor private static func observe() throws {
        _ = NSApplication.shared
        let args = Array(CommandLine.arguments.dropFirst())
        let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
        let executable = root.appendingPathComponent("dist/InternalKeyboardControl.app/Contents/MacOS/InternalKeyboardControl")
        guard args.count == 2, let pid = Int32(args[0]), pid > 0,
              let app = NSRunningApplication(processIdentifier: pid), !app.isTerminated,
              app.bundleIdentifier == "research.agentfreebrowser.internalkeyboardcontrol",
              app.executableURL?.resolvingSymlinksInPath() == executable.resolvingSymlinksInPath() else {
            throw NSError(domain: "OwnedWindowMetadata", code: 1, userInfo: [NSLocalizedDescriptionKey: "Require exact live research PID and recorded SHA256"])
        }
        let digest = SHA256.hash(data: try Data(contentsOf: executable)).map { String(format: "%02x", $0) }.joined()
        guard digest == args[1] else {
            throw NSError(domain: "OwnedWindowMetadata", code: 2, userInfo: [NSLocalizedDescriptionKey: "Research image hash changed"])
        }
        func owned(_ options: CGWindowListOption) -> [[String: Any]] {
            let windows = CGWindowListCopyWindowInfo(options, kCGNullWindowID) as? [[String: Any]] ?? []
            return windows.filter { ($0[kCGWindowOwnerPID as String] as? Int32) == pid }
        }
        let report: [String: Any] = ["pid": pid, "binarySHA256": digest,
                                    "allOwnedWindows": owned([.optionAll, .excludeDesktopElements]),
                                    "onScreenOwnedWindows": owned([.optionOnScreenOnly, .excludeDesktopElements]),
                                    "screenRecordingGranted": CGPreflightScreenCaptureAccess(),
                                    "frontmostIsTarget": NSWorkspace.shared.frontmostApplication?.processIdentifier == pid,
                                    "captureAttempted": false, "inputPosted": false]
        let data = try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
        print(String(decoding: data, as: UTF8.self))
    }
}

import AppKit
import CoreImage
import CoreMedia
import CryptoKit
import Darwin
import ImageIO
import ScreenCaptureKit
import UniformTypeIdentifiers

private struct ProbeError: Error, CustomStringConvertible {
    let description: String
    init(_ description: String) { self.description = description }
}

// The callback queue shares only immutable images and counters under this lock.
private final class Frames: NSObject, SCStreamOutput, @unchecked Sendable {
    private let lock = NSLock()
    private let context = CIContext()
    private var latest: CGImage?
    private var count = 0
    private var statuses: Set<Int> = []

    func stream(_ stream: SCStream, didOutputSampleBuffer sample: CMSampleBuffer, of type: SCStreamOutputType) {
        guard type == .screen, sample.isValid,
              let attachments = CMSampleBufferGetSampleAttachmentsArray(sample, createIfNecessary: false) as? [[SCStreamFrameInfo: Any]],
              let status = attachments.first?[.status] as? Int else { return }
        lock.withLock { _ = statuses.insert(status) }
        guard SCFrameStatus(rawValue: status) == .complete,
              let buffer = CMSampleBufferGetImageBuffer(sample) else { return }
        let image = CIImage(cvPixelBuffer: buffer)
        guard let copied = context.createCGImage(image, from: image.extent) else { return }
        lock.withLock { count += 1; latest = copied }
    }

    func snapshot() -> (count: Int, image: CGImage?, statuses: [Int]) {
        lock.withLock { (count, latest, statuses.sorted()) }
    }
}

@MainActor
private struct Target {
    let pid: pid_t
    let windowID: CGWindowID
    let digest: String
    let launchDate: Date
    let frame: CGRect

    static func identity(pid: pid_t, digest: String, root: URL) throws -> URL {
        let executable = root.appendingPathComponent("dist/InternalKeyboardControl.app/Contents/MacOS/InternalKeyboardControl")
        guard pid > 0, let app = NSRunningApplication(processIdentifier: pid), !app.isTerminated,
              app.bundleIdentifier == "research.agentfreebrowser.internalkeyboardcontrol",
              app.executableURL?.resolvingSymlinksInPath() == executable.resolvingSymlinksInPath() else {
            throw ProbeError("Target is not the exact owned InternalKeyboardControl app")
        }
        let actual = SHA256.hash(data: try Data(contentsOf: executable)).map { String(format: "%02x", $0) }.joined()
        guard actual == digest else { throw ProbeError("Target executable hash differs from the recorded session") }
        return executable
    }

    func verify(root: URL) throws {
        _ = try Self.identity(pid: pid, digest: digest, root: root)
        guard NSRunningApplication(processIdentifier: pid)?.launchDate == launchDate else {
            throw ProbeError("Target process identity changed")
        }
        let windows = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] ?? []
        guard let window = windows.first(where: { ($0[kCGWindowNumber as String] as? UInt32) == windowID }),
              (window[kCGWindowOwnerPID as String] as? Int32) == pid,
              (window[kCGWindowLayer as String] as? Int) == 0,
              let bounds = window[kCGWindowBounds as String] as? [String: Any],
              let current = CGRect(dictionaryRepresentation: bounds as CFDictionary), current == frame else {
            throw ProbeError("Owned window disappeared, moved, or changed size")
        }
    }
}

@main
private struct CaptureRefreshProbe {
    @MainActor static func main() async {
        signal(SIGALRM, SIG_DFL)
        alarm(30)
        _ = NSApplication.shared
        NSApp.setActivationPolicy(.prohibited)
        var report: [String: Any] = ["status": "refused", "probePID": getpid(), "systemInputPosted": false, "capturesAudio": false]
        var destination: URL?
        do {
            let args = Array(CommandLine.arguments.dropFirst())
            guard let outIndex = args.firstIndex(of: "--out"), outIndex == args.count - 2 else {
                throw ProbeError("Supply --out as the final argument")
            }
            let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
            let output = URL(fileURLWithPath: args[outIndex + 1]).standardizedFileURL
            let artifacts = root.appendingPathComponent("artifacts").resolvingSymlinksInPath().path + "/"
            guard output.resolvingSymlinksInPath().path.hasPrefix(artifacts), output.pathExtension == "json",
                  !FileManager.default.fileExists(atPath: output.path) else {
                throw ProbeError("Output must be a new JSON file within project artifacts")
            }
            try FileManager.default.createDirectory(at: output.deletingLastPathComponent(), withIntermediateDirectories: true,
                                                    attributes: [.posixPermissions: 0o700])
            destination = output
            let command = Array(args[..<outIndex])
            if command == ["--permissions"] {
                report["status"] = "preflight"
                report["screenRecordingGranted"] = CGPreflightScreenCaptureAccess()
            } else if command == ["--request-screen-recording"] {
                report["status"] = "requested"
                report["requestReturned"] = CGRequestScreenCaptureAccess()
                report["screenRecordingGranted"] = CGPreflightScreenCaptureAccess()
            } else {
                guard command.count == 4, command[0] == "sequence", let pid = Int32(command[1]),
                      let windowID = UInt32(command[2]), windowID > 0,
                      command[3].count == 64, command[3].allSatisfy({ "0123456789abcdef".contains($0) }) else {
                    throw ProbeError("Use sequence PID WINDOW_ID RECORDED_SHA256 --out ARTIFACT.json")
                }
                _ = try Target.identity(pid: pid, digest: command[3], root: root)
                guard CGPreflightScreenCaptureAccess() else { throw ProbeError("Screen Recording permission is absent") }
                try await capture(pid: pid, windowID: windowID, digest: command[3], root: root, output: output, report: &report)
            }
        } catch {
            report["error"] = String(describing: error)
        }
        do {
            let data = try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
            if let destination { try data.write(to: destination, options: [.withoutOverwriting]) }
            print(String(decoding: data, as: UTF8.self))
        } catch { fputs("Cannot write probe report\n", stderr) }
    }

    @MainActor private static func capture(pid: pid_t, windowID: CGWindowID, digest: String, root: URL,
                                          output: URL, report: inout [String: Any]) async throws {
        let content = try await SCShareableContent.excludingDesktopWindows(true, onScreenWindowsOnly: true)
        guard let window = content.windows.first(where: { $0.windowID == windowID && $0.owningApplication?.processID == pid }),
              let app = window.owningApplication, app.bundleIdentifier == "research.agentfreebrowser.internalkeyboardcontrol",
              let display = content.displays.first(where: { $0.frame.contains(window.frame) }),
              window.windowLayer == 0, window.frame.width >= 100, window.frame.height >= 100,
              window.frame.width <= 4096, window.frame.height <= 4096 else {
            throw ProbeError("Owned ordinary window is unavailable or outside one display")
        }
        _ = try Target.identity(pid: pid, digest: digest, root: root)
        guard let launchDate = NSRunningApplication(processIdentifier: pid)?.launchDate else {
            throw ProbeError("Target launch identity is unavailable")
        }
        let target = Target(pid: pid, windowID: windowID, digest: digest, launchDate: launchDate, frame: window.frame)
        try target.verify(root: root)
        let windowFilter = SCContentFilter(display: display, including: [window])
        let appFilter = SCContentFilter(display: display, including: [app],
                                        exceptingWindows: content.windows.filter { $0.owningApplication?.processID == pid && $0.windowID != windowID })
        let config = SCStreamConfiguration()
        config.sourceRect = window.frame.offsetBy(dx: -display.frame.minX, dy: -display.frame.minY)
        config.width = Int(window.frame.width * 2)
        config.height = Int(window.frame.height * 2)
        config.minimumFrameInterval = CMTime(value: 1, timescale: 30)
        config.queueDepth = 3
        config.showsCursor = false
        config.capturesAudio = false
        config.pixelFormat = kCVPixelFormatType_32BGRA
        let frames = Frames()
        let stream = SCStream(filter: windowFilter, configuration: config, delegate: nil)
        try stream.addStreamOutput(frames, type: .screen, sampleHandlerQueue: DispatchQueue(label: "research.filter-refresh"))
        var rows: [[String: Any]] = []
        report["targetPID"] = pid
        report["targetWindowID"] = windowID
        report["targetBinarySHA256"] = digest
        report["scope"] = "Owned diagnostic only. Sampled frames do not establish continuous exclusion. Queued frames can cross a filter update."
        var started = false
        do {
            for (index, name) in ["initial-window-filter", "updated-app-filter", "updated-window-filter"].enumerated() {
                try target.verify(root: root)
                let baseline = frames.snapshot().count
                if index == 0 { try await stream.startCapture(); started = true }
                else { try await stream.updateContentFilter(index == 1 ? appFilter : windowFilter) }
                var paths: [String] = []
                var previous = baseline
                for _ in 0..<20 {
                    try await Task.sleep(for: .milliseconds(100))
                    let snapshot = frames.snapshot()
                    if snapshot.count > previous, paths.count < 8, let image = snapshot.image {
                        let path = output.deletingPathExtension().appendingPathExtension("\(name)-\(paths.count).png")
                        guard !FileManager.default.fileExists(atPath: path.path),
                              let destination = CGImageDestinationCreateWithURL(path as CFURL, UTType.png.identifier as CFString, 1, nil) else {
                            throw ProbeError("Cannot create fresh PNG output")
                        }
                        CGImageDestinationAddImage(destination, image, nil)
                        guard CGImageDestinationFinalize(destination) else { throw ProbeError("PNG write failed") }
                        paths.append(path.path)
                        previous = snapshot.count
                    }
                }
                try target.verify(root: root)
                let snapshot = frames.snapshot()
                rows.append(["stage": name, "status": paths.isEmpty ? "inconclusive" : "sampled",
                             "completeFramesSinceBaseline": snapshot.count - baseline, "baselineCounter": baseline,
                             "statuses": snapshot.statuses, "images": paths])
                report["stages"] = rows
            }
            try await stream.stopCapture()
            started = false
            report["streamStopped"] = true
            report["status"] = rows.allSatisfy { ($0["status"] as? String) == "sampled" } ? "sampled" : "inconclusive"
        } catch {
            report["status"] = "inconclusive"
            if started {
                do { try await stream.stopCapture(); report["streamStopped"] = true }
                catch { report["streamStopped"] = false; report["stopError"] = String(describing: error) }
            }
            throw error
        }
    }
}

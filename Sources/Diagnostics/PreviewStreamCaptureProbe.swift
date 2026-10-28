import AppKit
import CoreImage
import CoreMedia
import Darwin
import ImageIO
import ScreenCaptureKit
import UniformTypeIdentifiers

private struct CaptureFailure: Error, CustomStringConvertible {
    let description: String
    init(_ description: String) { self.description = description }
}

// The callback queue shares immutable images and counters through this lock.
private final class StreamFrames: NSObject, SCStreamOutput, @unchecked Sendable {
    private let lock = NSLock()
    private let context = CIContext()
    private var complete = 0
    private var audited = 0
    private var colored = 0
    private var statuses: [Int: Int] = [:]
    private var latest: CGImage?
    private var firstColored: CGImage?

    func stream(_ stream: SCStream, didOutputSampleBuffer sample: CMSampleBuffer, of type: SCStreamOutputType) {
        guard type == .screen, sample.isValid,
              let attachments = CMSampleBufferGetSampleAttachmentsArray(sample, createIfNecessary: false) as? [[SCStreamFrameInfo: Any]],
              let rawStatus = attachments.first?[.status] as? Int else { return }
        lock.withLock { statuses[rawStatus, default: 0] += 1 }
        guard SCFrameStatus(rawValue: rawStatus) == .complete else { return }
        lock.withLock { complete += 1 }
        guard let buffer = CMSampleBufferGetImageBuffer(sample) else { return }
        guard CVPixelBufferGetPixelFormatType(buffer) == kCVPixelFormatType_32BGRA,
              CVPixelBufferLockBaseAddress(buffer, .readOnly) == kCVReturnSuccess else { return }
        defer { CVPixelBufferUnlockBaseAddress(buffer, .readOnly) }
        guard let base = CVPixelBufferGetBaseAddress(buffer) else { return }
        let bytes = UnsafeRawBufferPointer(start: base, count: CVPixelBufferGetDataSize(buffer))
        guard let hasColor = PreviewCapturePixels.containsColor(bytes, width: CVPixelBufferGetWidth(buffer),
                                                               height: CVPixelBufferGetHeight(buffer),
                                                               stride: CVPixelBufferGetBytesPerRow(buffer)) else { return }
        let image = CIImage(cvPixelBuffer: buffer)
        let copy = context.createCGImage(image, from: image.extent)
        lock.withLock {
            audited += 1
            if hasColor { colored += 1; if firstColored == nil { firstColored = copy } }
            latest = copy
        }
    }

    func snapshot() -> (complete: Int, audited: Int, colored: Int, latest: CGImage?, firstColored: CGImage?, statuses: [String: Int]) {
        lock.withLock { (complete, audited, colored, latest, firstColored,
                         Dictionary(uniqueKeysWithValues: statuses.map { (String($0.key), $0.value) })) }
    }
}

@main
private enum PreviewStreamCaptureProbe {
    @MainActor private static func verify(_ scope: PreviewAXScope, windowID: CGWindowID, frame: CGRect) throws {
        try scope.validate(scope.host)
        guard NSWorkspace.shared.frontmostApplication?.processIdentifier == scope.host.pid else {
            throw CaptureFailure("Research target lost foreground focus")
        }
        let rows = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] ?? []
        guard let row = rows.first(where: { ($0[kCGWindowNumber as String] as? UInt32) == windowID }),
              (row[kCGWindowOwnerPID as String] as? Int32) == scope.host.pid,
              (row[kCGWindowLayer as String] as? Int) == 0,
              (row[kCGWindowAlpha as String] as? Double) == 1,
              let bounds = row[kCGWindowBounds as String] as? [String: Any],
              CGRect(dictionaryRepresentation: bounds as CFDictionary) == frame else {
            throw CaptureFailure("Owned research window identity or geometry changed")
        }
    }

    private static func save(_ image: CGImage, to url: URL) throws {
        guard !FileManager.default.fileExists(atPath: url.path),
              let destination = CGImageDestinationCreateWithURL(url as CFURL, UTType.png.identifier as CFString, 1, nil) else {
            throw CaptureFailure("Use a new PNG within the report directory")
        }
        CGImageDestinationAddImage(destination, image, nil)
        guard CGImageDestinationFinalize(destination) else { throw CaptureFailure("PNG write failed") }
    }

    @MainActor private static func capture(mode: String, pid: pid_t, windowID: CGWindowID, root: URL,
                                           output: URL, report: inout [String: Any]) async throws {
        let scope = try PreviewAXScope(pid: pid, root: root)
        guard CGPreflightScreenCaptureAccess() else { throw CaptureFailure("Screen Recording permission is absent") }
        let content = try await SCShareableContent.excludingDesktopWindows(true, onScreenWindowsOnly: true)
        guard let window = content.windows.first(where: { $0.windowID == windowID && $0.owningApplication?.processID == pid }),
              let app = window.owningApplication, app.bundleIdentifier == scope.policy.bundle,
              let display = content.displays.first(where: { $0.frame.contains(window.frame) }),
              window.frame.width >= 400, window.frame.height >= 300,
              window.frame.width <= 4096, window.frame.height <= 4096 else {
            throw CaptureFailure("Owned research window is unavailable on one display")
        }
        let frame = window.frame
        try verify(scope, windowID: windowID, frame: frame)
        let filter = mode == "window" ? SCContentFilter(desktopIndependentWindow: window)
            : SCContentFilter(display: display, including: [app], exceptingWindows: [])
        filter.includeMenuBar = false
        let configuration = SCStreamConfiguration()
        configuration.width = Int(frame.width * 2)
        configuration.height = Int(frame.height * 2)
        if mode == "display" { configuration.sourceRect = frame.offsetBy(dx: -display.frame.minX, dy: -display.frame.minY) }
        configuration.minimumFrameInterval = CMTime(value: 1, timescale: 30)
        configuration.queueDepth = 3
        configuration.showsCursor = false
        configuration.capturesAudio = false
        configuration.pixelFormat = kCVPixelFormatType_32BGRA
        configuration.ignoreShadowsSingleWindow = true
        let frames = StreamFrames()
        let queue = DispatchQueue(label: "research.preview-stream-frames")
        let stream = SCStream(filter: filter, configuration: configuration, delegate: nil)
        try stream.addStreamOutput(frames, type: .screen, sampleHandlerQueue: queue)
        report["status"] = "inconclusive"
        report["targetPID"] = pid
        report["targetSHA256"] = scope.policy.digest
        report["windowID"] = windowID
        report["mode"] = mode
        report["filter"] = mode == "window" ? "Exact owned independent window" : "Only the exact owned research app, cropped to its window"
        report["configuredFPS"] = 30
        report["maximumSamples"] = 16
        report["durationSeconds"] = 30
        report["pixelPolicy"] = "Zero RGB and uniform alpha within each complete frame"
        var images: [String] = []
        var previous = 0
        var started = false
        let start = ProcessInfo.processInfo.systemUptime
        do {
            started = true
            try await stream.startCapture()
            for tick in 0..<300 {
                try await Task.sleep(for: .milliseconds(100))
                try verify(scope, windowID: windowID, frame: frame)
                let snapshot = frames.snapshot()
                if tick % 20 == 0, snapshot.audited > previous, images.count < 16, let image = snapshot.latest {
                    let path = output.deletingPathExtension().appendingPathExtension("sample-\(images.count).png")
                    try save(image, to: path)
                    images.append(path.path)
                    previous = snapshot.audited
                }
            }
            try await stream.stopCapture()
            started = false
            queue.sync {}
            try verify(scope, windowID: windowID, frame: frame)
            try scope.verifyImage()
            let snapshot = frames.snapshot()
            if let image = snapshot.firstColored {
                let path = output.deletingPathExtension().appendingPathExtension("first-colored.png")
                try save(image, to: path)
                report["firstColoredImage"] = path.path
            }
            report["completeFrames"] = snapshot.complete
            report["auditedFrames"] = snapshot.audited
            report["nonBlackFrames"] = snapshot.colored
            report["frameStatuses"] = snapshot.statuses
            report["images"] = images
            report["streamStopped"] = true
            report["elapsedSeconds"] = ProcessInfo.processInfo.systemUptime - start
            report["status"] = snapshot.complete > 0 && snapshot.complete == snapshot.audited ? "audited" : "inconclusive"
        } catch {
            if started {
                do { try await stream.stopCapture(); queue.sync {}; report["streamStopped"] = true }
                catch { report["streamStopped"] = false }
            }
            report["images"] = images
            throw error
        }
    }

    @MainActor static func main() async {
        signal(SIGALRM, SIG_DFL)
        alarm(45)
        _ = NSApplication.shared
        NSApp.setActivationPolicy(.prohibited)
        var report: [String: Any] = ["status": "refused", "inputPosted": false, "audioCaptured": false,
                                     "hooksInstalled": false, "permissionRequested": false, "probePID": getpid()]
        var output: URL?
        do {
            let args = Array(CommandLine.arguments.dropFirst())
            guard getuid() != 0, args.count >= 3, args[args.count - 2] == "--out" else {
                throw CaptureFailure("Use a command and a new --out report")
            }
            let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
            let destination = URL(fileURLWithPath: args.last!).standardizedFileURL
            guard destination.resolvingSymlinksInPath().path.hasPrefix(root.appendingPathComponent("artifacts").resolvingSymlinksInPath().path + "/"),
                  destination.pathExtension == "json", !FileManager.default.fileExists(atPath: destination.path) else {
                throw CaptureFailure("Use a new JSON file within project artifacts")
            }
            output = destination
            let command = Array(args.dropLast(2))
            if command == ["permissions"] {
                report["status"] = "preflight"
                report["screenRecordingGranted"] = CGPreflightScreenCaptureAccess()
            } else if command == ["request-screen-recording"] {
                report["permissionRequested"] = true
                report["status"] = "requested"
                report["requestReturned"] = CGRequestScreenCaptureAccess()
                report["screenRecordingGranted"] = CGPreflightScreenCaptureAccess()
            } else {
                guard command.count == 3, ["window", "display"].contains(command[0]),
                      let pid = Int32(command[1]), let windowID = UInt32(command[2]), windowID > 0 else {
                    throw CaptureFailure("Use window or display with the research PID and window ID")
                }
                try await capture(mode: command[0], pid: pid, windowID: windowID, root: root, output: destination, report: &report)
            }
        } catch {
            report["error"] = String(describing: error)
        }
        if let data = try? JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys]) {
            if let output { try? data.write(to: output, options: [.withoutOverwriting]) }
            print(String(decoding: data, as: UTF8.self))
        }
    }
}

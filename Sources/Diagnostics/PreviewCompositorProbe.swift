import AppKit
import CoreImage
import CoreMedia
import Darwin
import ImageIO
import ScreenCaptureKit
import UniformTypeIdentifiers

private struct CompositorFailure: Error, CustomStringConvertible {
    let description: String
    init(_ description: String) { self.description = description }
}

// The capture queue owns callbacks. This lock protects counters and immutable image copies.
private final class CompositorFrames: NSObject, SCStreamOutput, @unchecked Sendable {
    private let lock = NSLock()
    private let context = CIContext()
    private var complete = 0
    private var audited = 0
    private var nonuniform = 0
    private var latest: CGImage?
    private var firstNonuniform: CGImage?
    private var colors: Set<[UInt8]> = []

    func stream(_ stream: SCStream, didOutputSampleBuffer sample: CMSampleBuffer, of type: SCStreamOutputType) {
        guard type == .screen, sample.isValid,
              let attachments = CMSampleBufferGetSampleAttachmentsArray(sample, createIfNecessary: false) as? [[SCStreamFrameInfo: Any]],
              let status = attachments.first?[.status] as? Int,
              SCFrameStatus(rawValue: status) == .complete else { return }
        lock.withLock { complete += 1 }
        guard let buffer = CMSampleBufferGetImageBuffer(sample),
              CVPixelBufferGetPixelFormatType(buffer) == kCVPixelFormatType_32BGRA,
              CVPixelBufferLockBaseAddress(buffer, .readOnly) == kCVReturnSuccess else { return }
        defer { CVPixelBufferUnlockBaseAddress(buffer, .readOnly) }
        guard let base = CVPixelBufferGetBaseAddress(buffer),
              let color = PreviewCompositorPixels.uniformBGRA(
                UnsafeRawBufferPointer(start: base, count: CVPixelBufferGetDataSize(buffer)),
                width: CVPixelBufferGetWidth(buffer), height: CVPixelBufferGetHeight(buffer),
                stride: CVPixelBufferGetBytesPerRow(buffer)) else { return }
        let image = CIImage(cvPixelBuffer: buffer)
        let copy = context.createCGImage(image, from: image.extent)
        lock.withLock {
            audited += 1
            if color.isEmpty {
                nonuniform += 1
                if firstNonuniform == nil { firstNonuniform = copy }
            } else if colors.count < 32 { colors.insert(color) }
            latest = copy
        }
    }

    func snapshot() -> (complete: Int, audited: Int, nonuniform: Int, latest: CGImage?, first: CGImage?, colors: [[UInt8]]) {
        lock.withLock { (complete, audited, nonuniform, latest, firstNonuniform, colors.sorted { $0.lexicographicallyPrecedes($1) }) }
    }
}

@MainActor
private struct CompositorCoverage {
    let scope: PreviewAXScope
    let targetID: CGWindowID
    let backdropID: CGWindowID
    let frame: CGRect
    let region: CGRect

    func verify() throws {
        try scope.validate(scope.host)
        guard NSWorkspace.shared.frontmostApplication?.processIdentifier == scope.host.pid else {
            throw CompositorFailure("The research target lost foreground focus")
        }
        let rows = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] ?? []
        guard let targetIndex = rows.firstIndex(where: { ($0[kCGWindowNumber as String] as? UInt32) == targetID }),
              let backdropIndex = rows.firstIndex(where: { ($0[kCGWindowNumber as String] as? UInt32) == backdropID }),
              targetIndex < backdropIndex else { throw CompositorFailure("The research window ordering changed") }
        func bounds(_ row: [String: Any]) -> CGRect? {
            guard let raw = row[kCGWindowBounds as String] as? [String: Any] else { return nil }
            return CGRect(dictionaryRepresentation: raw as CFDictionary)
        }
        let target = rows[targetIndex], backdrop = rows[backdropIndex]
        guard (target[kCGWindowOwnerPID as String] as? Int32) == scope.host.pid,
              (backdrop[kCGWindowOwnerPID as String] as? Int32) == getpid(),
              (target[kCGWindowLayer as String] as? Int) == 0,
              (backdrop[kCGWindowLayer as String] as? Int) == 0,
              (target[kCGWindowAlpha as String] as? Double) == 1,
              (backdrop[kCGWindowAlpha as String] as? Double) == 1,
              (backdrop[kCGWindowSharingState as String] as? Int ?? 0) > 0,
              bounds(target) == frame, bounds(backdrop)?.contains(region) == true else {
            throw CompositorFailure("The opaque research coverage changed")
        }
        for row in rows.prefix(backdropIndex) {
            let id = row[kCGWindowNumber as String] as? UInt32
            if id == targetID || id == backdropID { continue }
            if (row[kCGWindowLayer as String] as? Int) == Int(CGWindowLevelForKey(.cursorWindow)) { continue }
            if (row[kCGWindowAlpha as String] as? Double ?? 1) > 0,
               let other = bounds(row), other.intersects(region) {
                throw CompositorFailure("Another window intersects the research region")
            }
        }
    }
}

@main
private enum PreviewCompositorProbe {
    private static func save(_ image: CGImage, to url: URL) throws {
        guard !FileManager.default.fileExists(atPath: url.path),
              let destination = CGImageDestinationCreateWithURL(url as CFURL, UTType.png.identifier as CFString, 1, nil) else {
            throw CompositorFailure("Use a new PNG in the report directory")
        }
        CGImageDestinationAddImage(destination, image, nil)
        guard CGImageDestinationFinalize(destination) else { throw CompositorFailure("PNG write failed") }
    }

    @MainActor private static func run(command: String, pid: pid_t, windowID: CGWindowID, root: URL,
                                      output: URL, report: inout [String: Any]) async throws {
        let scope = try PreviewAXScope(pid: pid, root: root)
        let rows = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] ?? []
        guard let row = rows.first(where: { ($0[kCGWindowNumber as String] as? UInt32) == windowID }),
              (row[kCGWindowOwnerPID as String] as? Int32) == pid,
              NSWorkspace.shared.frontmostApplication?.processIdentifier == pid,
              let bounds = row[kCGWindowBounds as String] as? [String: Any],
              let frame = CGRect(dictionaryRepresentation: bounds as CFDictionary),
              frame.width >= 600, frame.height >= 400, frame.width <= 4096, frame.height <= 4096,
              let main = NSScreen.screens.first else { throw CompositorFailure("The owned window geometry is unavailable") }
        let region = frame.insetBy(dx: 24, dy: 80)
        let backdropFrame = CGRect(x: frame.minX, y: main.frame.maxY - frame.maxY, width: frame.width, height: frame.height)
        let backdrop = NSWindow(contentRect: backdropFrame, styleMask: .borderless, backing: .buffered, defer: false)
        backdrop.isReleasedWhenClosed = false
        backdrop.isOpaque = true
        backdrop.backgroundColor = NSColor(srgbRed: 0.16, green: 0.37, blue: 0.58, alpha: 1)
        backdrop.ignoresMouseEvents = true
        backdrop.hasShadow = false
        backdrop.level = .normal
        backdrop.sharingType = .readOnly
        backdrop.title = "Owned capture backdrop"
        backdrop.order(.below, relativeTo: Int(windowID))
        defer { backdrop.close(); report["backdropClosed"] = true }
        try await Task.sleep(for: .milliseconds(200))
        let coverage = CompositorCoverage(scope: scope, targetID: windowID, backdropID: CGWindowID(backdrop.windowNumber), frame: frame, region: region)
        try coverage.verify()
        report["targetPID"] = pid
        report["targetSHA256"] = scope.policy.digest
        report["windowID"] = windowID
        report["crop"] = [region.minX, region.minY, region.width, region.height]
        report["coverageChecksAreAtomic"] = false
        if command == "coverage" {
            try scope.verifyImage()
            report["status"] = "coverage-verified"
            report["captureAttempted"] = false
            return
        }
        guard CGPreflightScreenCaptureAccess() else { throw CompositorFailure("Screen Recording permission is absent") }
        let content = try await SCShareableContent.excludingDesktopWindows(true, onScreenWindowsOnly: true)
        guard let window = content.windows.first(where: { $0.windowID == windowID && $0.owningApplication?.processID == pid }),
              let targetApp = window.owningApplication,
              let ownApp = content.applications.first(where: { $0.processID == getpid() }),
              let display = content.displays.first(where: { $0.frame.contains(frame) }),
              content.windows.contains(where: { $0.windowID == coverage.backdropID && $0.owningApplication?.processID == getpid() }) else {
            throw CompositorFailure("The research windows are not shareable on one display")
        }
        let unfiltered = SCContentFilter(display: display, excludingWindows: [])
        let ownedOnly = SCContentFilter(display: display, including: [targetApp, ownApp], exceptingWindows: [])
        unfiltered.includeMenuBar = false
        ownedOnly.includeMenuBar = false
        let config = SCStreamConfiguration()
        config.sourceRect = region.offsetBy(dx: -display.frame.minX, dy: -display.frame.minY)
        config.width = Int(region.width * 2)
        config.height = Int(region.height * 2)
        config.minimumFrameInterval = CMTime(value: 1, timescale: 30)
        config.queueDepth = 3
        config.showsCursor = false
        config.capturesAudio = false
        config.pixelFormat = kCVPixelFormatType_32BGRA
        let frames = CompositorFrames()
        let queue = DispatchQueue(label: "research.preview-compositor-frames")
        let stream = SCStream(filter: unfiltered, configuration: config, delegate: nil)
        try stream.addStreamOutput(frames, type: .screen, sampleHandlerQueue: queue)
        var started = false
        var stages: [[String: Any]] = []
        var images: [String] = []
        do {
            try coverage.verify()
            started = true
            try await stream.startCapture()
            for index in 0..<3 {
                let before = frames.snapshot()
                let stageStart = ProcessInfo.processInfo.systemUptime
                if index > 0 { try await stream.updateContentFilter(index == 1 ? ownedOnly : unfiltered) }
                for tick in 0..<30 {
                    try await Task.sleep(for: .milliseconds(100))
                    try coverage.verify()
                    if tick % 10 == 9, let image = frames.snapshot().latest {
                        let path = output.deletingPathExtension().appendingPathExtension("stage-\(index)-sample-\(tick / 10).png")
                        try save(image, to: path)
                        images.append(path.path)
                    }
                }
                let after = frames.snapshot()
                stages.append(["stage": index, "filter": index == 1 ? "owned-apps" : "unfiltered-display",
                               "completeFrames": after.complete - before.complete, "auditedFrames": after.audited - before.audited,
                               "nonuniformFrames": after.nonuniform - before.nonuniform,
                               "elapsedSeconds": ProcessInfo.processInfo.systemUptime - stageStart])
                report["stages"] = stages
            }
            try await stream.stopCapture()
            started = false
            queue.sync {}
            try coverage.verify()
            try scope.verifyImage()
            let all = frames.snapshot()
            if let image = all.first {
                let path = output.deletingPathExtension().appendingPathExtension("first-nonuniform.png")
                try save(image, to: path)
                report["firstNonuniformImage"] = path.path
            }
            report["completeFrames"] = all.complete
            report["auditedFrames"] = all.audited
            report["nonuniformFrames"] = all.nonuniform
            report["uniformBGRAColors"] = all.colors
            report["streamStopped"] = true
            report["status"] = all.complete > 0 && all.complete == all.audited ? "audited" : "inconclusive"
        } catch {
            if started {
                do { try await stream.stopCapture(); queue.sync {}; report["streamStopped"] = true }
                catch { report["streamStopped"] = false }
            }
            report["images"] = images
            throw error
        }
        report["images"] = images
    }

    @MainActor static func main() async {
        signal(SIGALRM, SIG_DFL)
        alarm(25)
        _ = NSApplication.shared
        NSApp.setActivationPolicy(.accessory)
        var report: [String: Any] = ["status": "refused", "inputPosted": false, "hooksInstalled": false,
                                     "audioCaptured": false, "permissionRequested": false, "probePID": getpid()]
        var output: URL?
        do {
            let args = Array(CommandLine.arguments.dropFirst())
            guard getuid() != 0, args.count >= 3, args[args.count - 2] == "--out" else {
                throw CompositorFailure("Use a command and a new --out report")
            }
            let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
            let destination = URL(fileURLWithPath: args.last!).standardizedFileURL
            guard destination.resolvingSymlinksInPath().path.hasPrefix(root.appendingPathComponent("artifacts").resolvingSymlinksInPath().path + "/"),
                  destination.pathExtension == "json", !FileManager.default.fileExists(atPath: destination.path) else {
                throw CompositorFailure("Use a new JSON file within project artifacts")
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
                guard command.count == 3, ["coverage", "sequence"].contains(command[0]),
                      let pid = Int32(command[1]), let windowID = UInt32(command[2]), windowID > 0 else {
                    throw CompositorFailure("Use coverage or sequence with the research PID and window ID")
                }
                try await run(command: command[0], pid: pid, windowID: windowID, root: root, output: destination, report: &report)
            }
        } catch { report["error"] = String(describing: error) }
        if let data = try? JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys]) {
            if let output { try? data.write(to: output, options: [.withoutOverwriting]) }
            print(String(decoding: data, as: UTF8.self))
        }
    }
}

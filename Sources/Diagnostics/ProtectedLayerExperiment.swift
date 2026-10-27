import AppKit
import AVFoundation
import CoreMedia
import CoreText
import CoreVideo
import VideoToolbox

struct RenderFailure: Error, CustomStringConvertible {
    let description: String
    init(_ description: String) { self.description = description }
}

@MainActor
private final class MediaPanel: NSView {
    let video = AVSampleBufferDisplayLayer()
    let marker = "AFB-" + UUID().uuidString.replacingOccurrences(of: "-", with: "").prefix(8)
    private let hosted: Bool
    private let compressed: Bool
    private var transfer: VTPixelTransferSession?
    private var encoder: H264Frames?
    private var frameNumber: Int64 = 0
    private var image: CGImage?

    init(frame: NSRect, protected: Bool, hosted: Bool, compressed: Bool) {
        self.hosted = hosted
        self.compressed = compressed
        super.init(frame: frame)
        video.preventsCapture = protected
        video.videoGravity = .resizeAspect
        video.backgroundColor = NSColor.black.cgColor
        if hosted {
            layer = video
            wantsLayer = true
        } else {
            wantsLayer = true
            layer?.addSublayer(video)
        }
    }

    required init?(coder: NSCoder) { nil }

    override func layout() {
        super.layout()
        if !hosted { video.frame = bounds }
    }

    func present() throws {
        if image == nil { image = try makePattern() }
        guard let image else { throw RenderFailure("Pattern image absent") }
        var bgra: CVPixelBuffer?
        guard CVPixelBufferCreate(kCFAllocatorDefault, 640, 360, kCVPixelFormatType_32BGRA,
            [kCVPixelBufferIOSurfacePropertiesKey: [:], kCVPixelBufferCGBitmapContextCompatibilityKey: true] as CFDictionary,
            &bgra) == kCVReturnSuccess, let bgra,
            CVPixelBufferLockBaseAddress(bgra, []) == kCVReturnSuccess else {
            throw RenderFailure("Pattern buffer allocation failed")
        }
        do {
            defer { CVPixelBufferUnlockBaseAddress(bgra, []) }
            guard let context = CGContext(data: CVPixelBufferGetBaseAddress(bgra), width: 640, height: 360,
                bitsPerComponent: 8, bytesPerRow: CVPixelBufferGetBytesPerRow(bgra), space: CGColorSpaceCreateDeviceRGB(),
                bitmapInfo: CGImageAlphaInfo.premultipliedFirst.rawValue | CGBitmapInfo.byteOrder32Little.rawValue) else {
                throw RenderFailure("Pattern buffer context failed")
            }
            context.draw(image, in: CGRect(x: 0, y: 0, width: 640, height: 360))
        }
        var nv12: CVPixelBuffer?
        guard CVPixelBufferCreate(kCFAllocatorDefault, 640, 360, kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange,
            [kCVPixelBufferIOSurfacePropertiesKey: [:]] as CFDictionary, &nv12) == kCVReturnSuccess, let nv12 else {
            throw RenderFailure("NV12 allocation failed")
        }
        if transfer == nil {
            guard VTPixelTransferSessionCreate(allocator: kCFAllocatorDefault, pixelTransferSessionOut: &transfer) == noErr else {
                throw RenderFailure("Transfer session failed")
            }
        }
        guard let transfer, VTPixelTransferSessionTransferImage(transfer, from: bgra, to: nv12) == noErr else {
            throw RenderFailure("Pattern conversion failed")
        }
        let sample: CMSampleBuffer
        if compressed {
            if encoder == nil { encoder = try H264Frames(width: 640, height: 360) }
            guard let encoder else { throw RenderFailure("Encoder absent") }
            sample = try encoder.encode(nv12)
        } else {
            var format: CMVideoFormatDescription?
            guard CMVideoFormatDescriptionCreateForImageBuffer(allocator: kCFAllocatorDefault, imageBuffer: nv12,
                formatDescriptionOut: &format) == noErr, let format else { throw RenderFailure("Raw format failed") }
            var timing = CMSampleTimingInfo(duration: CMTime(value: 1, timescale: 5),
                presentationTimeStamp: CMTime(value: frameNumber, timescale: 5), decodeTimeStamp: .invalid)
            var created: CMSampleBuffer?
            guard CMSampleBufferCreateReadyWithImageBuffer(allocator: kCFAllocatorDefault, imageBuffer: nv12,
                formatDescription: format, sampleTiming: &timing, sampleBufferOut: &created) == noErr, let created else {
                throw RenderFailure("Raw sample failed")
            }
            sample = created
        }
        guard let attachments = CMSampleBufferGetSampleAttachmentsArray(sample, createIfNecessary: true) as? [NSMutableDictionary],
              let first = attachments.first else { throw RenderFailure("Sample attachments absent") }
        first[kCMSampleAttachmentKey_DisplayImmediately] = true
        video.sampleBufferRenderer.enqueue(sample)
        guard video.sampleBufferRenderer.status != .failed else {
            throw RenderFailure(video.sampleBufferRenderer.error?.localizedDescription ?? "Presentation failed")
        }
        frameNumber += 1
    }

    var report: [String: Any] {
        ["marker": marker, "preventsCapture": video.preventsCapture, "hosted": hosted,
         "compressed": compressed, "frames": frameNumber, "ready": video.isReadyForDisplay,
         "obscured": video.isOutputObscuredDueToInsufficientExternalProtection,
         "rendererStatus": video.sampleBufferRenderer.status.rawValue,
         "viewBounds": [bounds.width, bounds.height],
         "layerBounds": [video.bounds.width, video.bounds.height],
         "rootLayerIsVideo": layer === video,
         "error": video.sampleBufferRenderer.error?.localizedDescription as Any? ?? NSNull()]
    }

    private func makePattern() throws -> CGImage {
        guard let context = CGContext(data: nil, width: 640, height: 360, bitsPerComponent: 8, bytesPerRow: 0,
            space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) else {
            throw RenderFailure("Pattern context failed")
        }
        context.setFillColor(CGColor(red: 0.93, green: 0.96, blue: 1, alpha: 1))
        context.fill(CGRect(x: 0, y: 0, width: 640, height: 360))
        let colors: [CGColor] = [NSColor.systemRed.cgColor, NSColor.systemGreen.cgColor, NSColor.systemBlue.cgColor]
        for (index, color) in colors.enumerated() {
            context.setFillColor(color)
            context.fill(CGRect(x: index * 214, y: 0, width: 214, height: 90))
        }
        let attributes: [NSAttributedString.Key: Any] = [
            NSAttributedString.Key(kCTFontAttributeName as String): CTFontCreateWithName("Menlo-Bold" as CFString, 40, nil),
            NSAttributedString.Key(kCTForegroundColorAttributeName as String): CGColor(gray: 0.08, alpha: 1),
        ]
        context.textPosition = CGPoint(x: 40, y: 220)
        CTLineDraw(CTLineCreateWithAttributedString(NSAttributedString(string: marker, attributes: attributes)), context)
        guard let image = context.makeImage() else { throw RenderFailure("Pattern image failed") }
        return image
    }
}

@MainActor
private final class LayerController: NSObject, NSApplicationDelegate {
    private var window: NSWindow!
    private var clear: MediaPanel!
    private var protected: MediaPanel!
    private var refresh: Task<Void, Never>?
    private let status = NSTextField(labelWithString: "Preparing paired media.")
    private var stateURL: URL?

    func applicationDidFinishLaunching(_ notification: Notification) {
        let args = CommandLine.arguments
        guard let index = args.firstIndex(of: "--state"), args.indices.contains(index + 1) else {
            NSApp.terminate(nil)
            return
        }
        stateURL = URL(fileURLWithPath: args[index + 1])
        let hosted = !args.contains("--sublayer")
        let compressed = !args.contains("--uncompressed")
        let mode = "\(hosted ? "Hosted" : "Sublayer") \(compressed ? "H264" : "NV12")"
        let content = NSView(frame: NSRect(x: 0, y: 0, width: 1120, height: 500))
        clear = MediaPanel(frame: NSRect(x: 20, y: 90, width: 520, height: 340), protected: false,
                           hosted: hosted, compressed: compressed)
        protected = MediaPanel(frame: NSRect(x: 580, y: 90, width: 520, height: 340), protected: true,
                               hosted: hosted, compressed: compressed)
        for (x, title) in [(20.0, "LEFT: Clear reference"), (580.0, "RIGHT: Protected trial")] {
            let label = NSTextField(labelWithString: title)
            label.font = .boldSystemFont(ofSize: 20)
            label.frame = NSRect(x: x, y: 445, width: 520, height: 30)
            content.addSubview(label)
        }
        content.addSubview(clear)
        content.addSubview(protected)
        status.frame = NSRect(x: 20, y: 20, width: 1080, height: 50)
        content.addSubview(status)
        window = NSWindow(contentRect: content.bounds, styleMask: [.titled, .closable, .miniaturizable],
                          backing: .buffered, defer: false)
        window.title = "Protected Layer Test: \(mode)"
        window.contentView = content
        window.center()
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        content.layoutSubtreeIfNeeded()
        for panel in [clear!, protected!] { panel.video.contentsScale = window.backingScaleFactor }
        print("LAYER_PROBE ready pid=\(getpid()) mode=\(mode)")
        fflush(stdout)
        refresh = Task { [weak self] in
            guard let self else { return }
            let deadline = ContinuousClock.now.advanced(by: .seconds(600))
            while !Task.isCancelled, ContinuousClock.now < deadline {
                do {
                    try clear.present()
                    try protected.present()
                    status.stringValue = "\(mode). Compare the two markers on the physical display. No browser or keyboard observer runs."
                    try save(mode: mode)
                    try await Task.sleep(for: .milliseconds(200))
                } catch {
                    if Task.isCancelled { return }
                    status.stringValue = "Media test stopped: \(error)"
                    try? save(mode: mode, error: String(describing: error))
                    return
                }
            }
            NSApp.terminate(nil)
        }
    }

    private func save(mode: String, error: String? = nil) throws {
        guard let stateURL else { throw RenderFailure("State path absent") }
        let data = try JSONSerialization.data(withJSONObject: ["pid": getpid(), "mode": mode,
            "clear": clear.report, "protected": protected.report,
            "failure": error as Any? ?? NSNull()], options: [.prettyPrinted, .sortedKeys])
        try data.write(to: stateURL, options: .atomic)
        try FileManager.default.setAttributes([.posixPermissions: 0o600], ofItemAtPath: stateURL.path)
    }

    func applicationWillTerminate(_ notification: Notification) { refresh?.cancel() }
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }
}

@main
enum ProtectedLayerApp {
    @MainActor static func main() {
        signal(SIGALRM, SIG_DFL)
        alarm(660)
        let app = NSApplication.shared
        let controller = LayerController()
        app.setActivationPolicy(.regular)
        app.delegate = controller
        withExtendedLifetime(controller) { app.run() }
    }
}

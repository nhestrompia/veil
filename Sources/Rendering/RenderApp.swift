import AppKit
import AVFoundation
import CoreMedia
import CoreVideo
import WebKit
import VideoToolbox

@MainActor
final class PixelDisplay: NSView {
    let display = AVSampleBufferDisplayLayer()
    private var transfer: VTPixelTransferSession?
    #if PIXEL_H264
    private var encoder: H264Frames?
    #endif

    init(protected: Bool) {
        super.init(frame: .zero)
        wantsLayer = true
        display.preventsCapture = protected
        display.videoGravity = .resize
        layer?.backgroundColor = NSColor.black.cgColor
        layer?.addSublayer(display)
    }

    required init?(coder: NSCoder) { nil }

    override func layout() {
        super.layout()
        display.frame = bounds
    }

    func present(_ image: CGImage) throws {
        var pixelBuffer: CVPixelBuffer?
        let attributes: [CFString: Any] = [kCVPixelBufferCGImageCompatibilityKey: true,
            kCVPixelBufferCGBitmapContextCompatibilityKey: true, kCVPixelBufferIOSurfacePropertiesKey: [:]]
        let allocation = CVPixelBufferCreate(kCFAllocatorDefault, image.width, image.height,
            kCVPixelFormatType_32BGRA, attributes as CFDictionary, &pixelBuffer)
        guard allocation == kCVReturnSuccess, let pixelBuffer else { throw RenderFailure("Pixel allocation failed") }
        guard CVPixelBufferLockBaseAddress(pixelBuffer, []) == kCVReturnSuccess else { throw RenderFailure("Pixel lock failed") }
        do {
            defer { CVPixelBufferUnlockBaseAddress(pixelBuffer, []) }
            guard let context = CGContext(data: CVPixelBufferGetBaseAddress(pixelBuffer), width: image.width,
                height: image.height, bitsPerComponent: 8, bytesPerRow: CVPixelBufferGetBytesPerRow(pixelBuffer),
                space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.premultipliedFirst.rawValue | CGBitmapInfo.byteOrder32Little.rawValue)
            else { throw RenderFailure("Pixel context failed") }
            context.draw(image, in: CGRect(x: 0, y: 0, width: image.width, height: image.height))
        }
        let renderBuffer: CVPixelBuffer
        #if PIXEL_NV12 || PIXEL_H264
        var converted: CVPixelBuffer?
        let nv12Attributes: [CFString: Any] = [kCVPixelBufferIOSurfacePropertiesKey: [:]]
        guard CVPixelBufferCreate(kCFAllocatorDefault, image.width, image.height,
            kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange, nv12Attributes as CFDictionary, &converted) == kCVReturnSuccess,
              let converted else { throw RenderFailure("NV12 allocation failed") }
        if transfer == nil {
            guard VTPixelTransferSessionCreate(allocator: kCFAllocatorDefault, pixelTransferSessionOut: &transfer) == noErr else {
                throw RenderFailure("Pixel transfer session failed")
            }
        }
        guard let transfer else { throw RenderFailure("Pixel transfer session missing") }
        let conversion = VTPixelTransferSessionTransferImage(transfer, from: pixelBuffer, to: converted)
        guard conversion == noErr else { throw RenderFailure("NV12 conversion failed: \(conversion)") }
        renderBuffer = converted
        #else
        renderBuffer = pixelBuffer
        #endif
        #if PIXEL_H264
        if encoder == nil {
            encoder = try H264Frames(width: CVPixelBufferGetWidth(renderBuffer), height: CVPixelBufferGetHeight(renderBuffer))
            print("PIXEL_RENDER codec=H264 hardwareEncoderRequired=true readbackStatus=\(encoder?.hardwareReadbackStatus ?? -1)")
            fflush(stdout)
        }
        guard let encoder else { throw RenderFailure("Compressed producer unavailable") }
        let sample = try encoder.encode(renderBuffer)
        #else
        var format: CMVideoFormatDescription?
        guard CMVideoFormatDescriptionCreateForImageBuffer(allocator: kCFAllocatorDefault, imageBuffer: renderBuffer,
            formatDescriptionOut: &format) == noErr, let format else { throw RenderFailure("Video format failed") }
        var timing = CMSampleTimingInfo(duration: .invalid, presentationTimeStamp: .zero, decodeTimeStamp: .invalid)
        var sample: CMSampleBuffer?
        guard CMSampleBufferCreateReadyWithImageBuffer(allocator: kCFAllocatorDefault, imageBuffer: renderBuffer,
            formatDescription: format, sampleTiming: &timing, sampleBufferOut: &sample) == noErr, let sample
        else { throw RenderFailure("Sample creation failed") }
        #endif
        guard let attachments = CMSampleBufferGetSampleAttachmentsArray(sample, createIfNecessary: true) as? [NSMutableDictionary],
              let attachment = attachments.first else { throw RenderFailure("Sample attachment missing") }
        attachment[kCMSampleAttachmentKey_DisplayImmediately] = true
        display.sampleBufferRenderer.enqueue(sample)
        if display.sampleBufferRenderer.status == .failed {
            throw RenderFailure(display.sampleBufferRenderer.error?.localizedDescription ?? "Renderer failed")
        }
    }

    func stop() { display.isHidden = true }
}

struct RenderFailure: Error, CustomStringConvertible {
    let description: String
    init(_ description: String) { self.description = description }
}

@MainActor
final class RenderController: NSObject, NSApplicationDelegate, WKNavigationDelegate {
    private var window: NSWindow!
    private var sourceWindow: NSWindow!
    private var webView: WKWebView!
    private var pixels: PixelDisplay!
    private let status = NSTextField(labelWithString: "Waiting for HTML snapshot. This renderer has no input bridge.")
    private var refreshTask: Task<Void, Never>?
    private var frames = 0

    func applicationDidFinishLaunching(_ notification: Notification) {
        #if PIXEL_PROTECTION
        let protected = true
        #if PIXEL_H264
        let name = "H264 Protection Experiment"
        #elseif PIXEL_NV12
        let name = "NV12 Protection Experiment"
        #else
        let name = "Pixel Protection Experiment"
        #endif
        #else
        let protected = false
        #if PIXEL_H264
        let name = "H264 Control"
        #elseif PIXEL_NV12
        let name = "NV12 Control"
        #else
        let name = "Pixel Control"
        #endif
        #endif
        pixels = PixelDisplay(protected: protected)
        let content = NSView()
        content.addSubview(pixels)
        content.addSubview(status)
        pixels.translatesAutoresizingMaskIntoConstraints = false
        status.translatesAutoresizingMaskIntoConstraints = false
        status.font = .systemFont(ofSize: 11)
        NSLayoutConstraint.activate([
            pixels.leadingAnchor.constraint(equalTo: content.leadingAnchor),
            pixels.trailingAnchor.constraint(equalTo: content.trailingAnchor),
            pixels.topAnchor.constraint(equalTo: content.topAnchor),
            pixels.bottomAnchor.constraint(equalTo: status.topAnchor, constant: -6),
            status.leadingAnchor.constraint(equalTo: content.leadingAnchor, constant: 12),
            status.bottomAnchor.constraint(equalTo: content.bottomAnchor, constant: -8),
        ])
        window = NSWindow(contentRect: NSRect(x: 100, y: 100, width: 1000, height: 740),
            styleMask: [.titled, .closable, .resizable, .miniaturizable], backing: .buffered, defer: false)
        window.title = name
        window.contentView = content
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)

        let configuration = WKWebViewConfiguration()
        configuration.websiteDataStore = .nonPersistent()
        webView = WKWebView(frame: NSRect(x: 0, y: 0, width: 1000, height: 700), configuration: configuration)
        webView.isInspectable = false
        webView.navigationDelegate = self
        webView.setAccessibilityHidden(true)
        // The source window never enters the visible window list or the onscreen compositor.
        sourceWindow = NSWindow(contentRect: webView.frame, styleMask: .borderless, backing: .buffered, defer: false)
        sourceWindow.contentView = webView
        sourceWindow.setAccessibilityHidden(true)

        let args = CommandLine.arguments
        guard let index = args.firstIndex(of: "--url"), args.indices.contains(index + 1),
              let url = BrowserPolicy.address(args[index + 1]) else {
            status.stringValue = "Supply --url with an HTTPS address or a loopback fixture."
            return
        }
        webView.load(URLRequest(url: url))
        print("PIXEL_RENDER ready pid=\(getpid()) preventsCapture=\(protected)")
        fflush(stdout)
    }

    func webView(_ webView: WKWebView, decidePolicyFor action: WKNavigationAction,
                 decisionHandler: @escaping @MainActor @Sendable (WKNavigationActionPolicy) -> Void) {
        decisionHandler(action.request.url.map(BrowserPolicy.allows) == true ? .allow : .cancel)
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        refreshTask?.cancel()
        refreshTask = Task { [weak self] in
            while !Task.isCancelled {
                guard let self else { return }
                do {
                    let configuration = WKSnapshotConfiguration()
                    configuration.afterScreenUpdates = false
                    let image = try await webView.takeSnapshot(configuration: configuration)
                    guard !Task.isCancelled else { return }
                    guard let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
                        throw RenderFailure("HTML snapshot has no image")
                    }
                    try pixels.present(cgImage)
                    frames += 1
                    status.stringValue = "HTML frames \(frames). Capture prevention \(pixels.display.preventsCapture). Input bridge absent."
                    if frames == 1 {
                        print("PIXEL_RENDER first_frame rendererStatus=\(pixels.display.sampleBufferRenderer.status.rawValue)")
                        fflush(stdout)
                    }
                    if frames == 5, #available(macOS 14.4, *) {
                        print("PIXEL_RENDER readiness ready=\(pixels.display.isReadyForDisplay) obscured=\(pixels.display.isOutputObscuredDueToInsufficientExternalProtection)")
                        fflush(stdout)
                    }
                    try await Task.sleep(for: .milliseconds(200))
                } catch {
                    if Task.isCancelled { return }
                    pixels.stop()
                    status.stringValue = "Renderer stopped. \(error.localizedDescription)"
                    print("PIXEL_RENDER failed \(error)")
                    fflush(stdout)
                    return
                }
            }
        }
    }

    func applicationWillTerminate(_ notification: Notification) { refreshTask?.cancel() }
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }
}

@main
enum RenderApp {
    @MainActor static func main() {
        #if PIXEL_H264
        if CommandLine.arguments.contains("--codec-smoke") {
            do {
                try CompressedSmoke.run()
            } catch {
                print("CODEC_SMOKE failed \(error)")
                exit(1)
            }
            return
        }
        #endif
        let app = NSApplication.shared
        let controller = RenderController()
        app.setActivationPolicy(.regular)
        app.delegate = controller
        withExtendedLifetime(controller) { app.run() }
    }
}

import AppKit

@MainActor
private final class ChannelDisplay: NSObject, NSApplicationDelegate {
    let channel: RendererChannel
    let fixture: URL
    private var window: NSWindow!
    private let pixels = NSImageView()
    private var poller: DispatchSourceTimer?
    private var freshness = RendererPacketFreshness()
    private var presented = 0
    private var stale = 0
    private var finished = false

    init(channel: RendererChannel, fixture: URL) { self.channel = channel; self.fixture = fixture }

    func applicationDidFinishLaunching(_ notification: Notification) {
        window = NSWindow(contentRect: NSRect(x: 100, y: 100, width: 800, height: 600),
                          styleMask: [.titled, .closable], backing: .buffered, defer: false)
        window.title = "Channel Display Control"
        window.contentView = pixels
        do {
            guard try channel.navigate(fixture) else { finish(error: "navigation-busy"); return }
        } catch { finish(error: "navigation-send"); return }
        ChannelProbeSupport.log("CHANNEL_DISPLAY_READY", ["host": ChannelProbeSupport.identity(), "rootRun": false])
        channel.watchReads { [weak self] in self?.poll() }
        let timer = DispatchSource.makeTimerSource(queue: .main)
        timer.schedule(deadline: .now(), repeating: .milliseconds(10))
        timer.setEventHandler { [weak self] in MainActor.assumeIsolated { self?.poll() } }
        poller = timer
        timer.resume()
        DispatchQueue.main.asyncAfter(deadline: .now() + 8) { [self] in finish() }
    }

    private func poll() {
        guard !finished else { return }
        channel.flush()
        do {
            for packet in try channel.receive() {
                guard packet.kind == .pixels else { finish(error: "unexpected-kind"); return }
                guard freshness.accept(packet, now: RendererChannel.now(), maximumAge: 500_000_000) else {
                    stale += 1
                    ChannelProbeSupport.log("CHANNEL_FRAME_EXPIRED", ["sequence": packet.sequence,
                        "issuedNanoseconds": packet.issuedNanoseconds, "receivedNanoseconds": RendererChannel.now()])
                    continue
                }
                guard packet.payload.starts(with: [137, 80, 78, 71, 13, 10, 26, 10]),
                      let image = NSImage(data: packet.payload), let bitmap = NSBitmapImageRep(data: packet.payload),
                      bitmap.pixelsWide >= 800, bitmap.pixelsHigh >= 600,
                      bitmap.pixelsWide * 600 == bitmap.pixelsHigh * 800,
                      let white = bitmap.colorAt(x: bitmap.pixelsWide - 10, y: bitmap.pixelsHigh - 10)?.usingColorSpace(.sRGB),
                      white.redComponent > 0.95, white.greenComponent > 0.95, white.blueComponent > 0.95 else {
                    finish(error: "invalid-pixels"); return
                }
                pixels.image = image
                presented += 1
                ChannelProbeSupport.log("CHANNEL_FRAME_PRESENTED", ["count": presented, "sequence": packet.sequence,
                    "presentedNanoseconds": RendererChannel.now(), "issuedNanoseconds": packet.issuedNanoseconds])
            }
        } catch { finish(error: String(describing: error)) }
    }

    private func finish(error: String? = nil) {
        guard !finished else { return }
        finished = true
        poller?.cancel()
        var result: [String: Any] = ["completed": error == nil, "presented": presented, "staleFrames": stale,
            "visibleWindows": NSApp.windows.filter(\.isVisible).count, "rootRun": false]
        if let error { result["error"] = error }
        ChannelProbeSupport.log("CHANNEL_DISPLAY_RESULT", result)
        channel.close()
        NSApp.terminate(nil)
    }
}

@main
private enum ChannelDisplayMain {
    @MainActor static func main() {
        guard let (fd, fixture) = ChannelProbeSupport.arguments(), let channel = try? RendererChannel(descriptor: fd) else { exit(64) }
        let app = NSApplication.shared
        app.setActivationPolicy(.prohibited)
        let delegate = ChannelDisplay(channel: channel, fixture: fixture)
        app.delegate = delegate
        withExtendedLifetime(delegate) { app.run() }
    }
}

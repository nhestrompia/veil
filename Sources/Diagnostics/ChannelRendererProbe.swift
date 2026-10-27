import AppKit
import WebKit

@MainActor
private final class ChannelRenderer: NSObject, NSApplicationDelegate, WKNavigationDelegate {
    let channel: RendererChannel
    let fixture: URL
    private var view: WKWebView!
    private var poller: DispatchSourceTimer?
    private var freshness = RendererPacketFreshness()
    private var busy = false
    private var loaded = false
    private var finished = false
    private var nextSnapshot: UInt64 = 0
    private var frames = 0
    private var refusedCommands = 0
    private var acceptedCommands = 0
    #if CHANNEL_IDENTITY_CONTROL
    private var initialRoles: [String: [String: Any]] = [:]
    #endif

    init(channel: RendererChannel, fixture: URL) { self.channel = channel; self.fixture = fixture }

    func applicationDidFinishLaunching(_ notification: Notification) {
        let configuration = WKWebViewConfiguration()
        configuration.websiteDataStore = .nonPersistent()
        configuration.preferences.javaScriptCanOpenWindowsAutomatically = false
        guard BrowserRuntimePolicy.configureContent(configuration) else { finish(error: "content-policy"); return }
        view = WKWebView(frame: NSRect(x: 0, y: 0, width: 800, height: 600), configuration: configuration)
        view.isInspectable = false
        view.navigationDelegate = self
        channel.watchReads { [weak self] in self?.poll() }
        let timer = DispatchSource.makeTimerSource(queue: .main)
        timer.schedule(deadline: .now(), repeating: .milliseconds(10))
        timer.setEventHandler { [weak self] in MainActor.assumeIsolated { self?.poll() } }
        poller = timer
        timer.resume()
        DispatchQueue.main.asyncAfter(deadline: .now() + 11) { [self] in finish() }
        ChannelProbeSupport.log("CHANNEL_RENDERER_READY", ["host": ChannelProbeSupport.identity(), "rootRun": false])
    }

    private func poll() {
        guard !finished else { return }
        do {
            for packet in try channel.receive() {
                guard packet.kind == .navigation,
                      freshness.accept(packet, now: RendererChannel.now(), maximumAge: 250_000_000),
                      let text = String(data: packet.payload, encoding: .utf8), text == fixture.absoluteString else {
                    refusedCommands += 1
                    continue
                }
                acceptedCommands += 1
                view.load(URLRequest(url: fixture, cachePolicy: .reloadIgnoringLocalCacheData))
            }
        } catch {
            refusedCommands += 1
            channel.close()
        }
        channel.flush()
        let now = RendererChannel.now()
        guard loaded, !busy, now >= nextSnapshot else { return }
        nextSnapshot = now + 100_000_000
        busy = true
        Task { @MainActor in
            defer { busy = false }
            do {
                let started = RendererChannel.now()
                let sample = try await view.callAsyncJavaScript("return {nonce:window.fixtureNonce,ticks:window.fixtureTicks};",
                    arguments: [:], in: nil, contentWorld: .page) as? [String: Any] ?? [:]
                let image = try await view.takeSnapshot(configuration: nil)
                guard !finished, let tiff = image.tiffRepresentation, let bitmap = NSBitmapImageRep(data: tiff),
                      let png = bitmap.representation(using: .png, properties: [:]) else { return }
                try channel.offerPixels(png)
                frames += 1
                #if CHANNEL_IDENTITY_CONTROL
                if frames == 1 {
                    initialRoles = ChannelProbeSupport.roleIdentities(view)
                    ChannelProbeSupport.log("CHANNEL_ATTACK_READY", ["host": ChannelProbeSupport.identity(),
                        "services": initialRoles, "sample": sample, "readyNanoseconds": RendererChannel.now()])
                }
                #endif
                ChannelProbeSupport.log("CHANNEL_FRAME_PRODUCED", ["frame": frames, "sample": sample,
                    "startedNanoseconds": started, "finishedNanoseconds": RendererChannel.now(),
                    "wouldBlock": channel.wouldBlock, "replacedFrames": channel.replacedFrames,
                    "peakBufferedBytes": channel.peakBufferedBytes, "channelClosed": channel.closed,
                    "pngBytes": png.count])
            } catch { finish(error: String(describing: error)) }
        }
    }

    func webView(_ webView: WKWebView, decidePolicyFor action: WKNavigationAction) async -> WKNavigationActionPolicy {
        action.request.url == fixture ? .allow : .cancel
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) { loaded = true }

    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: any Error) {
        finish(error: String(describing: error))
    }

    private func finish(error: String? = nil) {
        guard !finished else { return }
        finished = true
        poller?.cancel()
        var result: [String: Any] = ["completed": error == nil, "frames": frames,
            "acceptedCommands": acceptedCommands, "refusedCommands": refusedCommands,
            "rolePIDs": view.map(ChannelProbeSupport.roles) ?? [:], "host": ChannelProbeSupport.identity(),
            "wouldBlock": channel.wouldBlock, "replacedFrames": channel.replacedFrames,
            "peakBufferedBytes": channel.peakBufferedBytes, "channelClosed": channel.closed,
            "visibleWindows": NSApp.windows.filter(\.isVisible).count, "rootRun": false]
        if let error { result["error"] = error }
        #if CHANNEL_IDENTITY_CONTROL
        let finalRoles = view.map(ChannelProbeSupport.roleIdentities) ?? [:]
        result["services"] = finalRoles
        result["serviceIdentitiesStable"] = !initialRoles.isEmpty && NSDictionary(dictionary: initialRoles).isEqual(to: finalRoles)
        #endif
        ChannelProbeSupport.log("CHANNEL_RENDERER_RESULT", result)
        channel.close()
        view?.stopLoading()
        view = nil
        NSApp.terminate(nil)
    }
}

@main
private enum ChannelRendererMain {
    @MainActor static func main() {
        guard let (fd, fixture) = ChannelProbeSupport.arguments(), BrowserRuntimePolicy.disableDeveloperExtras(),
              let channel = try? RendererChannel(descriptor: fd) else { exit(64) }
        let app = NSApplication.shared
        app.setActivationPolicy(.prohibited)
        let delegate = ChannelRenderer(channel: channel, fixture: fixture)
        app.delegate = delegate
        withExtendedLifetime(delegate) { app.run() }
    }
}

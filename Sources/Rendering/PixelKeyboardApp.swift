#if PIXEL_KEYBOARD
import AppKit
import WebKit
import IOKit.hid

@MainActor
final class PixelKeyboardController: NSObject, NSApplicationDelegate, WKNavigationDelegate, NSTextFieldDelegate {
    private var window: AXBoundaryWindow!
    private var webView: AXBoundaryWebView!
    private var pixels: PixelDisplay!
    private let address = DeviceAddressField(string: "")
    private let status = NSTextField(labelWithString: "Press Space, then Return. Mouse input is disabled.")
    private var keyboard: DeviceKeyboardRouter?
    private var keyboardBound = false
    private var refreshTask: Task<Void, Never>?
    private var placeholder: CGImage?
    private var frames = 0
    #if PIXEL_ROUTING_CONTROL
    private var calibrationStarted = false
    #endif

    func applicationDidFinishLaunching(_ notification: Notification) {
        #if PIXEL_COMPOSITING_CONTROL
        let protected = true
        let isolatedSource = CommandLine.arguments.contains("--source-only-clipping")
        let name = isolatedSource ? "Compositing: clipped source" : "Compositing: clipped root"
        #elseif PIXEL_ROUTING_CONTROL
        let protected = false
        let name = "Keyboard Routing Control"
        #else
        let protected = true
        let name = "Protected Keyboard Browser"
        #endif
        pixels = PixelDisplay(protected: protected)
        let content = NSView()
        #if PIXEL_COMPOSITING_CONTROL
        let sources: NSView
        if isolatedSource {
            sources = NSView(frame: NSRect(x: 0, y: 0, width: 1000, height: 740))
            sources.autoresizingMask = [.width, .height]
            sources.wantsLayer = true
            sources.layer?.masksToBounds = true
            content.addSubview(sources)
        } else {
            sources = content
            content.wantsLayer = true
            content.layer?.masksToBounds = true
        }
        #else
        let sources = content
        content.wantsLayer = true
        content.layer?.masksToBounds = true
        #endif
        content.addSubview(pixels)
        content.addSubview(status)
        pixels.translatesAutoresizingMaskIntoConstraints = false
        status.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            pixels.leadingAnchor.constraint(equalTo: content.leadingAnchor),
            pixels.trailingAnchor.constraint(equalTo: content.trailingAnchor),
            pixels.topAnchor.constraint(equalTo: content.topAnchor),
            pixels.bottomAnchor.constraint(equalTo: status.topAnchor, constant: -6),
            status.leadingAnchor.constraint(equalTo: content.leadingAnchor, constant: 12),
            status.bottomAnchor.constraint(equalTo: content.bottomAnchor, constant: -8),
        ])
        window = AXBoundaryWindow(contentRect: NSRect(x: 100, y: 100, width: 1000, height: 740),
            styleMask: [.titled, .closable, .resizable, .miniaturizable], backing: .buffered, defer: false)
        window.title = name
        window.contentView = content
        let configuration = WKWebViewConfiguration()
        configuration.websiteDataStore = .nonPersistent()
        configuration.preferences.javaScriptCanOpenWindowsAutomatically = false
        guard BrowserRuntimePolicy.disableDeveloperExtras(), BrowserRuntimePolicy.configureContent(configuration) else {
            status.stringValue = "Required content restrictions are unavailable."
            window.makeKeyAndOrderFront(nil)
            return
        }
        webView = AXBoundaryWebView(frame: NSRect(x: -1200, y: -1000, width: 1000, height: 700), configuration: configuration)
        webView.isInspectable = false
        webView.navigationDelegate = self
        webView.setAccessibilityHidden(true)
        sources.addSubview(webView)
        address.frame = NSRect(x: -1200, y: -1100, width: 1000, height: 40)
        address.delegate = self
        address.setAccessibilityHidden(true)
        sources.addSubview(address)
        let args = CommandLine.arguments
        if let index = args.firstIndex(of: "--url"), args.indices.contains(index + 1) {
            address.stringValue = args[index + 1]
        }
        let menu = NSMenu()
        let item = NSMenuItem()
        let appMenu = NSMenu()
        appMenu.addItem(withTitle: "Quit", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        item.submenu = appMenu
        menu.addItem(item)
        NSApp.mainMenu = menu
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        window.makeFirstResponder(address)
        (NSApp as? DeviceKeyboardApplication)?.onOpenLocation = { [weak self] in self?.focusAddress() }
        keyboard = DeviceKeyboardRouter(window: window) { [weak self] in self?.didBindKeyboard() }
        keyboard?.start()
        if IOHIDCheckAccess(kIOHIDRequestTypeListenEvent) != kIOHIDAccessTypeGranted {
            status.stringValue = "Input Monitoring is required. Command-Tab switches to another app."
        }
        print("PIXEL_RENDER ready pid=\(getpid()) preventsCapture=\(protected) pendingPhysicalSubmit=true")
        fflush(stdout)
        startRefresh()
        #if PIXEL_ROUTING_CONTROL
        didBindKeyboard()
        Task { [weak self] in
            try? await Task.sleep(for: .milliseconds(300))
            self?.calibrationKey(36, character: "\r")
        }
        #endif
    }

    private func focusAddress() {
        window.makeFirstResponder(address)
        address.selectText(nil)
    }

    private func didBindKeyboard() {
        keyboardBound = true
        status.stringValue = "Keyboard ready. Press Return. Command-L edits the address."
        focusAddress()
    }

    func control(_ control: NSControl, textView: NSTextView, doCommandBy selector: Selector) -> Bool {
        guard control === address, selector == #selector(NSResponder.insertNewline(_:)) else { return false }
        navigate()
        return true
    }

    private func navigate() {
        guard keyboardBound, let url = BrowserPolicy.address(address.stringValue) else {
            print("PIXEL_NAVIGATION_REFUSED bound=\(keyboardBound)")
            fflush(stdout)
            return
        }
        (NSApp as? DeviceKeyboardApplication)?.didBeginNavigation()
        webView.load(URLRequest(url: url))
        print("PIXEL_NAVIGATION deviceBound=true pageFocus=\(window.makeFirstResponder(webView))")
        fflush(stdout)
    }

    func application(_ application: NSApplication, open urls: [URL]) {
        print("PIXEL_NAVIGATION externalOpenRefused=true")
        fflush(stdout)
    }

    func webView(_ webView: WKWebView, decidePolicyFor action: WKNavigationAction,
                 decisionHandler: @escaping @MainActor @Sendable (WKNavigationActionPolicy) -> Void) {
        guard keyboardBound, let url = action.request.url,
              BrowserPolicy.allowsNavigation(url, isMainFrame: action.targetFrame?.isMainFrame != false),
              !action.shouldPerformDownload, action.targetFrame != nil else {
            decisionHandler(.cancel)
            return
        }
        decisionHandler(.allow)
    }

    func webView(_ webView: WKWebView, decidePolicyFor response: WKNavigationResponse,
                 decisionHandler: @escaping @MainActor @Sendable (WKNavigationResponsePolicy) -> Void) {
        let disposition = (response.response as? HTTPURLResponse)?.value(forHTTPHeaderField: "Content-Disposition")
        decisionHandler(BrowserPolicy.allowsResponse(url: response.response.url,
            canShowMIMEType: response.canShowMIMEType, contentDisposition: disposition,
            isMainFrame: response.isForMainFrame) ? .allow : .cancel)
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        #if PIXEL_ROUTING_CONTROL
        guard !calibrationStarted else { return }
        calibrationStarted = true
        Task { [weak self] in
            guard let self else { return }
            try? await Task.sleep(for: .milliseconds(500))
            calibrationKey(48, character: "\t")
            let keys: [(UInt16, String)] = [(45,"n"),(0,"a"),(17,"t"),(34,"i"),(9,"v"),(14,"e"),(27,"-"),
                                           (34,"i"),(45,"n"),(35,"p"),(32,"u"),(17,"t")]
            for (key, text) in keys {
                try? await Task.sleep(for: .milliseconds(80))
                calibrationKey(key, character: text)
            }
            calibrationKey(36, character: "\r")
            print("PIXEL_ROUTING_CALIBRATION sequenceFinished=true")
            fflush(stdout)
        }
        #endif
    }

    private func startRefresh() {
        refreshTask = Task { [weak self] in
            while !Task.isCancelled {
                guard let self else { return }
                do {
                    let image: CGImage
                    if webView.url == nil {
                        if placeholder == nil {
                            let scale = window.backingScaleFactor
                            guard let context = CGContext(data: nil, width: Int(1000 * scale), height: Int(700 * scale),
                                bitsPerComponent: 8, bytesPerRow: 0, space: CGColorSpaceCreateDeviceRGB(),
                                bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) else {
                                throw RenderFailure("Preview allocation failed")
                            }
                            context.setFillColor(CGColor(gray: 1, alpha: 1))
                            context.fill(CGRect(x: 0, y: 0, width: context.width, height: context.height))
                            placeholder = context.makeImage()
                        }
                        guard let placeholder else { throw RenderFailure("Preview image unavailable") }
                        image = placeholder
                    } else {
                        let configuration = WKSnapshotConfiguration()
                        configuration.afterScreenUpdates = false
                        let snapshot = try await webView.takeSnapshot(configuration: configuration)
                        guard !Task.isCancelled else { return }
                        guard let value = snapshot.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
                            throw RenderFailure("HTML snapshot has no image")
                        }
                        image = value
                    }
                    try pixels.present(image, address: address.stringValue)
                    frames += 1
                    if frames == 5 {
                        print("PIXEL_RENDER readiness frames=\(frames)")
                        #if PIXEL_COMPOSITING_CONTROL
                        print("PIXEL_COMPOSITING sourceOnlyClipping=\(CommandLine.arguments.contains("--source-only-clipping")) ready=\(pixels.display.isReadyForDisplay) obscured=\(pixels.display.isOutputObscuredDueToInsufficientExternalProtection) rendererStatus=\(pixels.display.sampleBufferRenderer.status.rawValue)")
                        #endif
                        fflush(stdout)
                    }
                    try await Task.sleep(for: .milliseconds(200))
                } catch {
                    if Task.isCancelled { return }
                    pixels.stop()
                    status.stringValue = "Rendering stopped."
                    print("PIXEL_RENDER failed \(error)")
                    fflush(stdout)
                    return
                }
            }
        }
    }

    #if PIXEL_ROUTING_CONTROL
    private func calibrationKey(_ key: UInt16, character: String) {
        for down in [true, false] {
            guard let event = NSEvent.keyEvent(with: down ? .keyDown : .keyUp, location: .zero,
                modifierFlags: [], timestamp: ProcessInfo.processInfo.systemUptime,
                windowNumber: window.windowNumber, context: nil, characters: character,
                charactersIgnoringModifiers: character, isARepeat: false, keyCode: key) else { return }
            (NSApp as? DeviceKeyboardApplication)?.dispatchDeviceEvent(event)
        }
    }
    #endif

    func applicationWillResignActive(_ notification: Notification) { keyboard?.resetPending() }
    func applicationWillTerminate(_ notification: Notification) {
        refreshTask?.cancel()
        keyboard?.stop()
    }
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }
}

@main
enum PixelKeyboardApp {
    @MainActor static func main() {
        if CommandLine.arguments.contains("--request-input-monitoring") {
            print("PIXEL_INPUT requested=\(IOHIDRequestAccess(kIOHIDRequestTypeListenEvent))")
            return
        }
        if CommandLine.arguments.contains("--permissions") {
            print("PIXEL_INPUT listenGranted=\(IOHIDCheckAccess(kIOHIDRequestTypeListenEvent) == kIOHIDAccessTypeGranted)")
            return
        }
        let app = DeviceKeyboardApplication.shared
        let controller = PixelKeyboardController()
        app.setActivationPolicy(.regular)
        app.delegate = controller
        withExtendedLifetime(controller) { app.run() }
    }
}
#endif

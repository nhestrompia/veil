import AppKit
import WebKit
import Carbon
#if DEVICE_KEYBOARD_EXPERIMENT
import IOKit.hidsystem
#endif

@MainActor
final class BrowserController: NSObject, NSApplicationDelegate, WKNavigationDelegate, WKUIDelegate {
    private var window: NSWindow!
    private var webView: WKWebView!
    #if DEVICE_KEYBOARD_EXPERIMENT
    private let address = DeviceAddressField()
    #else
    private let address = NSTextField()
    #endif
    private let status = NSTextField(labelWithString: "Research build. Desktop agents are not blocked.")
    private let back = NSButton(title: "Back", target: nil, action: nil)
    private let forward = NSButton(title: "Forward", target: nil, action: nil)
    private let reload = NSButton(title: "Reload", target: nil, action: nil)
    private var navigationObservations: [NSKeyValueObservation] = []
    private var navigationNote = ""
    private var ownsSecureInput = false
    #if DEVICE_KEYBOARD_EXPERIMENT
    private var deviceKeyboard: DeviceKeyboardRouter?
    #endif

    func applicationDidFinishLaunching(_ notification: Notification) {
        let configuration = WKWebViewConfiguration()
        configuration.websiteDataStore = .nonPersistent()
        configuration.preferences.javaScriptCanOpenWindowsAutomatically = false
        #if !INSPECTION_CONTROL
        guard BrowserRuntimePolicy.configureContent(configuration) else {
            print("Browser startup refused: required content restrictions are unavailable.")
            NSApp.terminate(nil)
            return
        }
        #endif
        #if AX_BOUNDARY_EXPERIMENT || DEVICE_KEYBOARD_EXPERIMENT
        webView = AXBoundaryWebView(frame: .zero, configuration: configuration)
        #elseif !INSPECTION_CONTROL
        webView = RestrictedWebView(frame: .zero, configuration: configuration)
        #else
        webView = WKWebView(frame: .zero, configuration: configuration)
        #endif
        #if INSPECTION_CONTROL
        webView.isInspectable = true
        let name = "Inspectable Control"
        #else
        webView.isInspectable = false
        #if METADATA_EXPERIMENT
        let name = "Input Source Experiment"
        #elseif SECURE_INPUT_EXPERIMENT
        let name = "Secure Input Experiment"
        #elseif REDUCED_EXPOSURE_EXPERIMENT
        let name = "Reduced Exposure Experiment"
        #elseif AX_BOUNDARY_EXPERIMENT
        let name = "AX Boundary Experiment"
        #elseif DEVICE_KEYBOARD_EXPERIMENT
        let name = "Device Keyboard Experiment"
        #else
        let name = "AgentFreeBrowser Research"
        #endif
        #endif
        #if !INSPECTION_CONTROL
        guard BrowserRuntimePolicy.contentIsRestricted(webView.configuration) else {
            print("Browser startup refused: effective content restrictions failed readback.")
            NSApp.terminate(nil)
            return
        }
        #endif
        webView.navigationDelegate = self
        webView.uiDelegate = self

        address.placeholderString = "Enter an HTTPS address"
        address.target = self
        address.action = #selector(navigate)
        address.setAccessibilityLabel("Website address")
        back.target = self
        back.action = #selector(goBack)
        forward.target = self
        forward.action = #selector(goForward)
        reload.target = self
        reload.action = #selector(reloadPage)
        let bar = NSStackView(views: [back, forward, address, reload])
        bar.spacing = 8
        status.font = .systemFont(ofSize: 11)
        status.textColor = .secondaryLabelColor
        let content = NSView()
        for view in [bar, webView!, status] {
            content.addSubview(view)
            view.translatesAutoresizingMaskIntoConstraints = false
        }
        NSLayoutConstraint.activate([
            bar.leadingAnchor.constraint(equalTo: content.leadingAnchor, constant: 12),
            bar.trailingAnchor.constraint(equalTo: content.trailingAnchor, constant: -12),
            bar.topAnchor.constraint(equalTo: content.topAnchor, constant: 10),
            address.widthAnchor.constraint(greaterThanOrEqualToConstant: 400),
            webView.topAnchor.constraint(equalTo: bar.bottomAnchor, constant: 10),
            webView.leadingAnchor.constraint(equalTo: content.leadingAnchor),
            webView.trailingAnchor.constraint(equalTo: content.trailingAnchor),
            webView.bottomAnchor.constraint(equalTo: status.topAnchor, constant: -6),
            status.leadingAnchor.constraint(equalTo: content.leadingAnchor, constant: 12),
            status.trailingAnchor.constraint(equalTo: content.trailingAnchor, constant: -12),
            status.bottomAnchor.constraint(equalTo: content.bottomAnchor, constant: -8),
        ])
        let frame = NSRect(x: 100, y: 100, width: 1000, height: 740)
        let style: NSWindow.StyleMask = [.titled, .closable, .miniaturizable, .resizable]
        #if METADATA_EXPERIMENT
        window = InputSourceWindow(contentRect: frame, styleMask: style, backing: .buffered, defer: false)
        #elseif SECURE_INPUT_EXPERIMENT || REDUCED_EXPOSURE_EXPERIMENT
        window = SecureInputWindow(contentRect: frame, styleMask: style, backing: .buffered, defer: false)
        #elseif AX_BOUNDARY_EXPERIMENT || DEVICE_KEYBOARD_EXPERIMENT
        window = AXBoundaryWindow(contentRect: frame, styleMask: style, backing: .buffered, defer: false)
        #else
        window = NSWindow(contentRect: frame, styleMask: style, backing: .buffered, defer: false)
        #endif
        window.title = name
        #if REDUCED_EXPOSURE_EXPERIMENT || AX_BOUNDARY_EXPERIMENT || DEVICE_KEYBOARD_EXPERIMENT
        webView.setAccessibilityHidden(true)
        #if !DEVICE_VISIBLE_CONTROL
        window.sharingType = .none
        #endif
        #endif
        window.contentView = content
        observeNavigation()
        #if !BROWSER_NAVIGATION_CONTROL
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        #endif
        let menu = NSMenu()
        let appItem = NSMenuItem()
        let appMenu = NSMenu()
        appMenu.addItem(withTitle: "Quit " + name, action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        appItem.submenu = appMenu
        menu.addItem(appItem)
        #if !DEVICE_KEYBOARD_EXPERIMENT
        let fileItem = NSMenuItem()
        let fileMenu = NSMenu(title: "File")
        let openLocation = NSMenuItem(title: "Open Location", action: #selector(focusAddress), keyEquivalent: "l")
        openLocation.target = self
        fileMenu.addItem(openLocation)
        fileItem.submenu = fileMenu
        menu.addItem(fileItem)
        let editItem = NSMenuItem()
        let editMenu = NSMenu(title: "Edit")
        for (title, selector, key) in [("Cut", "cut:", "x"), ("Copy", "copy:", "c"), ("Paste", "paste:", "v"), ("Select All", "selectAll:", "a")] {
            editMenu.addItem(withTitle: title, action: Selector(selector), keyEquivalent: key)
        }
        editItem.submenu = editMenu
        menu.addItem(editItem)
        #else
        (NSApp as? DeviceKeyboardApplication)?.onOpenLocation = { [weak self] in self?.focusAddress() }
        #endif
        NSApp.mainMenu = menu

        let arguments = CommandLine.arguments
        if let index = arguments.firstIndex(of: "--url"), arguments.indices.contains(index + 1) {
            address.stringValue = arguments[index + 1]
            #if DEVICE_KEYBOARD_EXPERIMENT
            status.stringValue = "Built-in keyboard only. Press Space, then Return to open this address. Mouse input is disabled."
            window.makeFirstResponder(address)
            print("STARTUP_ADDRESS pendingPhysicalSubmit=true")
            #else
            navigate()
            #endif
        } else {
            window.makeFirstResponder(address)
        }
        print("Browser ready: pid=\(ProcessInfo.processInfo.processIdentifier) inspectable=\(webView.isInspectable)")
        #if DEVICE_KEYBOARD_EXPERIMENT
        deviceKeyboard = DeviceKeyboardRouter(window: window) { [weak self] in
            guard let self else { return }
            self.status.stringValue = "Keyboard ready. Press Return to open the address. Mouse input is disabled."
            self.focusAddress()
        }
        deviceKeyboard?.start()
        #endif
        fflush(stdout)
    }

    @objc private func navigate() {
        guard let url = BrowserPolicy.address(address.stringValue) else {
            status.stringValue = "Use HTTPS, or loopback HTTP for a research fixture."
            return
        }
        #if DEVICE_KEYBOARD_EXPERIMENT
        (NSApp as? DeviceKeyboardApplication)?.didBeginNavigation()
        #endif
        webView.load(URLRequest(url: url))
        window.makeFirstResponder(webView)
    }

    private func observeNavigation() {
        let properties: [KeyPath<WKWebView, Bool>] = [\.canGoBack, \.canGoForward, \.isLoading]
        navigationObservations = properties.map { property in
            webView.observe(property, options: [.initial, .new]) { [weak self] _, _ in
                MainActor.assumeIsolated { self?.updateNavigation() }
            }
        }
    }

    private func updateNavigation() {
        back.isEnabled = webView.canGoBack
        forward.isEnabled = webView.canGoForward
        reload.isEnabled = webView.isLoading || webView.url != nil
        reload.title = webView.isLoading ? "Stop" : "Reload"
        window.subtitle = webView.isLoading ? "Loading page" : navigationNote
    }

    @objc private func goBack() { if webView.canGoBack { webView.goBack() } }
    @objc private func goForward() { if webView.canGoForward { webView.goForward() } }
    @objc private func reloadPage() {
        if webView.isLoading {
            navigationNote = "Page load stopped."
            webView.stopLoading()
        } else {
            webView.reload()
        }
        updateNavigation()
    }
    @objc private func focusAddress() {
        window.makeFirstResponder(address)
        address.selectText(nil)
    }

    func webView(_ webView: WKWebView, decidePolicyFor navigationAction: WKNavigationAction,
                 decisionHandler: @escaping @MainActor @Sendable (WKNavigationActionPolicy) -> Void) {
        guard let url = navigationAction.request.url,
              BrowserPolicy.allowsNavigation(url, isMainFrame: navigationAction.targetFrame?.isMainFrame != false),
              !navigationAction.shouldPerformDownload else {
            status.stringValue = "Navigation refused by the research policy."
            decisionHandler(.cancel)
            return
        }
        decisionHandler(.allow)
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        navigationNote = ""
        updateNavigation()
        address.stringValue = webView.url?.absoluteString ?? ""
        status.stringValue = "Inspection: \(webView.isInspectable ? "control enabled" : "disabled"). Desktop capture and input: unprotected."
        #if METADATA_EXPERIMENT
        status.stringValue = "Experimental HID-state filter. Physical human origin is not established."
        #endif
        #if SECURE_INPUT_EXPERIMENT || REDUCED_EXPOSURE_EXPERIMENT
        status.stringValue = "Secure Event Input experiment. Synthetic input prevention is unproven."
        #endif
        #if AX_BOUNDARY_EXPERIMENT
        status.stringValue = "Accessibility boundary experiment. Native input prevention is unproven."
        #endif
        #if DEVICE_KEYBOARD_EXPERIMENT
        status.stringValue = "Built-in keyboard only. Command-L selects the address. Mouse input is disabled. US ASCII only. Research build."
        #endif
    }

    func webView(_ webView: WKWebView, didStartProvisionalNavigation navigation: WKNavigation!) {
        navigationNote = ""
        updateNavigation()
    }

    func webView(_ webView: WKWebView, didCommit navigation: WKNavigation!) {
        if let url = webView.url { address.stringValue = url.absoluteString }
    }

    func webView(_ webView: WKWebView, decidePolicyFor navigationResponse: WKNavigationResponse,
                 decisionHandler: @escaping @MainActor @Sendable (WKNavigationResponsePolicy) -> Void) {
        let response = navigationResponse.response
        let disposition = (response as? HTTPURLResponse)?.value(forHTTPHeaderField: "Content-Disposition")
        let allowed = BrowserPolicy.allowsResponse(url: response.url,
            canShowMIMEType: navigationResponse.canShowMIMEType, contentDisposition: disposition,
            isMainFrame: navigationResponse.isForMainFrame)
        if !allowed { status.stringValue = "Download or unsupported response refused by the research policy." }
        decisionHandler(allowed ? .allow : .cancel)
    }

    func webView(_ webView: WKWebView, navigationAction: WKNavigationAction, didBecome download: WKDownload) {
        download.cancel { _ in }
    }

    func webView(_ webView: WKWebView, navigationResponse: WKNavigationResponse, didBecome download: WKDownload) {
        download.cancel { _ in }
    }

    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: any Error) {
        recordNavigationError(error)
    }

    func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: any Error) {
        recordNavigationError(error)
    }

    private func recordNavigationError(_ error: any Error) {
        let failure = error as NSError
        if failure.domain != NSURLErrorDomain || failure.code != NSURLErrorCancelled {
            navigationNote = error.localizedDescription
        }
        updateNavigation()
    }

    func webViewWebContentProcessDidTerminate(_ webView: WKWebView) {
        navigationNote = "Page process stopped. Reload to recover."
        updateNavigation()
    }

    func webView(_ webView: WKWebView, createWebViewWith configuration: WKWebViewConfiguration,
                 for navigationAction: WKNavigationAction, windowFeatures: WKWindowFeatures) -> WKWebView? {
        if let url = navigationAction.request.url, BrowserPolicy.allows(url) {
            webView.load(navigationAction.request)
        }
        return nil
    }

    func webView(_ webView: WKWebView, runOpenPanelWith parameters: WKOpenPanelParameters,
                 initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping @MainActor @Sendable ([URL]?) -> Void) {
        completionHandler(nil)
        status.stringValue = "File upload is unavailable in this research build."
    }

    func webView(_ webView: WKWebView, requestMediaCapturePermissionFor origin: WKSecurityOrigin,
                 initiatedByFrame frame: WKFrameInfo, type: WKMediaCaptureType,
                 decisionHandler: @escaping @MainActor @Sendable (WKPermissionDecision) -> Void) {
        decisionHandler(.deny)
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }

    func applicationDidBecomeActive(_ notification: Notification) {
        #if SECURE_INPUT_EXPERIMENT || REDUCED_EXPOSURE_EXPERIMENT
        if !ownsSecureInput {
            let result = EnableSecureEventInput()
            ownsSecureInput = result == noErr
            print("SECURE_INPUT enabled=\(ownsSecureInput) status=\(result) effective=\(IsSecureEventInputEnabled())")
            fflush(stdout)
        }
        #endif
    }

    func applicationWillResignActive(_ notification: Notification) {
        releaseSecureInput()
        #if DEVICE_KEYBOARD_EXPERIMENT
        deviceKeyboard?.resetPending()
        #endif
    }
    func applicationWillTerminate(_ notification: Notification) {
        releaseSecureInput()
        #if DEVICE_KEYBOARD_EXPERIMENT
        deviceKeyboard?.stop()
        #endif
    }

    private func releaseSecureInput() {
        if ownsSecureInput {
            let result = DisableSecureEventInput()
            ownsSecureInput = false
            print("SECURE_INPUT released status=\(result)")
            fflush(stdout)
        }
    }
}

#if !BROWSER_NAVIGATION_CONTROL
@main
enum BrowserApp {
    @MainActor static func main() {
        #if !INSPECTION_CONTROL
        guard BrowserRuntimePolicy.disableDeveloperExtras() else {
            print("Browser startup refused: local developer tools remain enabled.")
            return
        }
        #endif
        #if DEVICE_KEYBOARD_EXPERIMENT
        let app = DeviceKeyboardApplication.shared
        precondition(app is DeviceKeyboardApplication, "The device experiment requires its application subclass")
        if CommandLine.arguments.contains("--permissions") || CommandLine.arguments.contains("--request-permissions") {
            if CommandLine.arguments.contains("--request-permissions") {
                _ = IOHIDRequestAccess(kIOHIDRequestTypeListenEvent)
            }
            print("DEVICE_KEYBOARD permission=\(IOHIDCheckAccess(kIOHIDRequestTypeListenEvent) == kIOHIDAccessTypeGranted)")
            return
        }
        #elseif AX_BOUNDARY_EXPERIMENT
        let app = AXBoundaryApplication.shared
        precondition(app is AXBoundaryApplication, "The AX experiment requires its application subclass")
        print("AX_BOUNDARY applicationSubclass=true")
        #else
        let app = NSApplication.shared
        #endif
        let delegate = BrowserController()
        app.setActivationPolicy(.regular)
        app.delegate = delegate
        withExtendedLifetime(delegate) { app.run() }
    }
}
#endif

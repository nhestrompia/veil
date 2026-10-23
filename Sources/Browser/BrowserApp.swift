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
    private let address = NSTextField()
    private let status = NSTextField(labelWithString: "Research build. Desktop agents are not blocked.")
    private var ownsSecureInput = false
    #if DEVICE_KEYBOARD_EXPERIMENT
    private var deviceKeyboard: DeviceKeyboardRouter?
    #endif

    func applicationDidFinishLaunching(_ notification: Notification) {
        let configuration = WKWebViewConfiguration()
        configuration.websiteDataStore = .nonPersistent()
        configuration.preferences.javaScriptCanOpenWindowsAutomatically = false
        #if AX_BOUNDARY_EXPERIMENT || DEVICE_KEYBOARD_EXPERIMENT
        webView = AXBoundaryWebView(frame: .zero, configuration: configuration)
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
        webView.navigationDelegate = self
        webView.uiDelegate = self

        address.placeholderString = "Enter an HTTPS address"
        address.target = self
        address.action = #selector(navigate)
        address.setAccessibilityLabel("Website address")
        let back = NSButton(title: "Back", target: self, action: #selector(goBack))
        let reload = NSButton(title: "Reload", target: self, action: #selector(reloadPage))
        let bar = NSStackView(views: [back, address, reload])
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
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        let menu = NSMenu()
        let appItem = NSMenuItem()
        let appMenu = NSMenu()
        appMenu.addItem(withTitle: "Quit " + name, action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        appItem.submenu = appMenu
        menu.addItem(appItem)
        #if !DEVICE_KEYBOARD_EXPERIMENT
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
            status.stringValue = "Press physical Space to bind the keyboard, then Return to open this address. Mouse input is disabled."
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

    @objc private func goBack() { webView.goBack() }
    @objc private func reloadPage() { webView.reload() }
    @objc private func focusAddress() {
        window.makeFirstResponder(address)
        address.selectText(nil)
    }

    func webView(_ webView: WKWebView, decidePolicyFor navigationAction: WKNavigationAction,
                 decisionHandler: @escaping @MainActor @Sendable (WKNavigationActionPolicy) -> Void) {
        guard let url = navigationAction.request.url, BrowserPolicy.allows(url), !navigationAction.shouldPerformDownload else {
            status.stringValue = "Navigation refused by the research policy."
            decisionHandler(.cancel)
            return
        }
        decisionHandler(.allow)
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
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
        status.stringValue = "Keyboard only. Command-L selects the address. Mouse input is disabled. US ASCII only. Research build."
        #endif
    }

    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: any Error) {
        status.stringValue = error.localizedDescription
    }

    func webViewWebContentProcessDidTerminate(_ webView: WKWebView) {
        status.stringValue = "Page process stopped. Reload to recover."
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

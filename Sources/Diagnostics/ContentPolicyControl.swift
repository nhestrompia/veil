import AppKit
import WebKit

@main
enum ContentPolicyControl {
    @MainActor static func main() throws {
        let arguments = CommandLine.arguments
        guard let index = arguments.firstIndex(of: "--out"), arguments.indices.contains(index + 1) else {
            throw CocoaError(.fileWriteInvalidFileName)
        }
        _ = NSApplication.shared
        let configuration = WKWebViewConfiguration()
        configuration.websiteDataStore = .nonPersistent()
        let before = BrowserRuntimePolicy.featureState(in: configuration.preferences, disable: false)
        let accepted = BrowserRuntimePolicy.configureContent(configuration)
        let after = BrowserRuntimePolicy.featureState(in: configuration.preferences, disable: false)
        var report: [String: Any] = [
            "scope": "Installed engine preference calibration. No external attack or human control.",
            "macOS": ProcessInfo.processInfo.operatingSystemVersionString,
            "before": before as Any? ?? NSNull(), "after": after as Any? ?? NSNull(),
            "policyAccepted": accepted,
            "requiredFeatures": BrowserRuntimePolicy.deniedFeatures,
            "missingFeatures": BrowserRuntimePolicy.deniedFeatures.filter { after?[$0] == nil },
            "fullscreenDisabled": !configuration.preferences.isElementFullscreenEnabled
        ]
        report["unknownFeatureRefused"] = !BrowserRuntimePolicy.configureContent(WKWebViewConfiguration(), requiredFeatures: ["MissingResearchFeature"])
        let view = RestrictedWebView(frame: .zero, configuration: configuration)
        report["effectiveConfigurationRestricted"] = BrowserRuntimePolicy.contentIsRestricted(view.configuration)
        if #available(macOS 15.0, *) {
            report["writingToolsDisabled"] = configuration.value(forKey: "writingToolsBehavior") as? Int == NSWritingToolsBehavior.none.rawValue
        }
        let output = URL(fileURLWithPath: arguments[index + 1])
        guard arguments.contains("--page-check") else { return try write(report, to: output) }
        let controlConfiguration = WKWebViewConfiguration()
        controlConfiguration.websiteDataStore = .nonPersistent()
        let control = WKWebView(frame: .zero, configuration: controlConfiguration)
        let window = NSWindow(contentRect: NSRect(x: 120, y: 120, width: 900, height: 600),
                              styleMask: [.titled, .closable], backing: .buffered, defer: false)
        window.title = "Content policy diagnostic"
        let stack = NSStackView(views: [control, view])
        stack.orientation = .vertical
        stack.distribution = .fillEqually
        window.contentView = stack
        NSApp.setActivationPolicy(.regular)
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        let html = "<html><body><p>AFB-EXPORT-CONTROL</p><input aria-label='Diagnostic editor'></body></html>"
        for page in [control, view] { page.loadHTMLString(html, baseURL: URL(string: "https://example.invalid")) }
        Task { @MainActor in
            try? await Task.sleep(for: .seconds(20))
            try? write(["status": "inconclusive", "reason": "Diagnostic watchdog expired"], to: output)
            exit(2)
        }
        Task { @MainActor in
            do {
                for page in [control, view] {
                    var loaded = false
                    for _ in 0..<50 {
                        if let ready = try? await page.evaluateJavaScript("document.readyState === 'complete' && document.body?.textContent.includes('AFB-EXPORT-CONTROL')"), ready as? Bool == true {
                            loaded = true
                            break
                        }
                        try await Task.sleep(for: .milliseconds(100))
                    }
                    guard loaded else { throw NSError(domain: "ResearchContentPolicy", code: 2,
                        userInfo: [NSLocalizedDescriptionKey: "The diagnostic page did not load"]) }
                }
                report["controlPage"] = try await inspectPage(control, window: window)
                report["restrictedPage"] = try await inspectPage(view, window: window)
                report["status"] = "observed"
                try write(report, to: output)
                window.close()
                exit(0)
            } catch {
                report["status"] = "inconclusive"
                report["error"] = String(describing: error)
                try? write(report, to: output)
                window.close()
                exit(2)
            }
        }
        NSApp.run()
    }

    @MainActor private static func inspectPage(_ view: WKWebView, window: NSWindow) async throws -> [String: Any] {
        window.makeFirstResponder(view)
        guard let exposure = try await view.evaluateJavaScript("({secure:isSecureContext,share:typeof navigator.share,clipboard:typeof navigator.clipboard,publicKey:typeof PublicKeyCredential,payment:typeof PaymentRequest,applePay:typeof ApplePaySession})") as? [String: Any] else {
            throw NSError(domain: "ResearchContentPolicy", code: 1,
                          userInfo: [NSLocalizedDescriptionKey: "WebKit returned no interface observation"])
        }
        let nativeSelectionAccepted = NSApp.sendAction(NSSelectorFromString("selectAll:"), to: view, from: nil)
        try await Task.sleep(for: .milliseconds(100))
        let selectionHasMarker = try await view.evaluateJavaScript("getSelection().toString().includes('AFB-EXPORT-CONTROL')") as? Bool == true
        let board = NSPasteboard(name: NSPasteboard.Name("research.agentfreebrowser.export.\(UUID().uuidString)"))
        defer { board.releaseGlobally() }
        board.setString("research-sentinel", forType: .string)
        let selector = NSSelectorFromString("writeSelectionToPasteboard:types:")
        guard view.responds(to: selector), let implementation = view.method(for: selector) else {
            return ["interfaces": exposure, "selectionWriterAvailable": false]
        }
        // The signature matches WebKit's native Services selection writer.
        typealias WriteSelection = @convention(c) (AnyObject, Selector, NSPasteboard, NSArray) -> Bool
        let writeSelection = unsafeBitCast(implementation, to: WriteSelection.self)
        let written = writeSelection(view, selector, board, [NSPasteboard.PasteboardType.string.rawValue] as NSArray)
        let text = board.string(forType: .string)
        return ["interfaces": exposure, "selectionWriterAvailable": true, "selectionWriteAccepted": written,
                "selectionHasMarker": selectionHasMarker,
                "nativeSelectionAccepted": nativeSelectionAccepted,
                "namedPasteboardTypes": (board.types ?? []).map(\.rawValue),
                "namedPasteboardStringLength": text?.count as Any? ?? NSNull(),
                "namedPasteboardMarkerRecovered": text?.contains("AFB-EXPORT-CONTROL") == true,
                "namedPasteboardUnchanged": text == "research-sentinel",
                "servicesRequestorAvailable": view.validRequestor(forSendType: .string, returnType: .string) != nil,
                "effectivePreferences": BrowserRuntimePolicy.featureState(in: view.configuration.preferences, disable: false) as Any? ?? NSNull(),
                "generalPasteboardRead": false, "generalPasteboardWritten": false]
    }

    private static func write(_ report: [String: Any], to output: URL) throws {
        let data = try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
        try data.write(to: output, options: .atomic)
    }
}

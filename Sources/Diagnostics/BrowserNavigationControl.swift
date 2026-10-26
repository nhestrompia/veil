import AppKit
import WebKit
import ObjectiveC.runtime
import Darwin

@MainActor
private final class NavigationDriver: NSObject, NSApplicationDelegate {
    private let browser = BrowserController()
    private var finished = false
    private var checks: [String: Bool] = [:]
    private var page: WKWebView?

    func applicationDidFinishLaunching(_ notification: Notification) {
        browser.applicationDidFinishLaunching(notification)
        DispatchQueue.main.asyncAfter(deadline: .now() + 25) { [self] in finish(error: "navigation-control-deadline") }
        Task { @MainActor in
            do { try await run() }
            catch { finish(error: String(describing: error)) }
        }
    }

    private func descendants(_ view: NSView) -> [NSView] {
        [view] + view.subviews.flatMap { descendants($0) }
    }

    private func require(_ value: Bool, _ name: String) throws {
        checks[name] = value
        if !value { throw NSError(domain: name, code: 1) }
    }

    private func wait(_ condition: @MainActor () async throws -> Bool) async throws {
        let deadline = ProcessInfo.processInfo.systemUptime + 7
        while !(try await condition()) {
            if ProcessInfo.processInfo.systemUptime >= deadline {
                throw NSError(domain: "navigation-control-wait", code: 2)
            }
            try await Task.sleep(for: .milliseconds(20))
        }
    }

    private func submit(_ field: NSTextField, _ url: URL) throws {
        field.stringValue = url.absoluteString
        guard let action = field.action, field.sendAction(action, to: field.target) else {
            throw NSError(domain: "address-control-action", code: 3)
        }
    }

    private func visit(_ view: WKWebView) async throws -> Int {
        let value = try await view.callAsyncJavaScript("return window.fixtureVisit;", arguments: [:], in: nil, contentWorld: .page)
        return value as? Int ?? -1
    }

    private func run() async throws {
        let args = CommandLine.arguments
        guard args.count == 3, args[1] == "--fixture", let base = URL(string: args[2]),
              base.scheme == "http", base.host == "127.0.0.1", let port = base.port,
              (1024...65535).contains(port), base.user == nil, base.password == nil,
              base.query == nil, base.fragment == nil,
              base.path.range(of: "\\A/navigation/[0-9a-f]{16}\\z", options: .regularExpression) != nil,
              let window = NSApp.windows.first(where: { $0.title == "AgentFreeBrowser Research" }),
              let content = window.contentView else {
            throw NSError(domain: "navigation-control-setup", code: 4)
        }
        let views = descendants(content)
        guard let view = views.compactMap({ $0 as? WKWebView }).first,
              let field = views.compactMap({ $0 as? NSTextField }).first(where: { $0.placeholderString != nil }),
              let back = views.compactMap({ $0 as? NSButton }).first(where: { $0.title == "Back" }),
              let forward = views.compactMap({ $0 as? NSButton }).first(where: { $0.title == "Forward" }),
              let reload = views.compactMap({ $0 as? NSButton }).first(where: { $0.title == "Reload" }) else {
            throw NSError(domain: "navigation-controls-missing", code: 5)
        }
        page = view
        try require(!back.isEnabled && !forward.isEnabled && !reload.isEnabled, "empty-history-controls")
        let a = base.appendingPathComponent("a"), b = base.appendingPathComponent("b")
        try submit(field, a)
        try await wait { !view.isLoading && view.url == a && reload.isEnabled }
        try require(!back.isEnabled && !forward.isEnabled, "first-page-history")
        try submit(field, b)
        try await wait { !view.isLoading && view.url == b && back.isEnabled }
        back.performClick(nil)
        try await wait { !view.isLoading && view.url == a && forward.isEnabled }
        try require(field.stringValue == a.absoluteString, "back-address")
        forward.performClick(nil)
        try await wait { !view.isLoading && view.url == b && !forward.isEnabled }
        try require(field.stringValue == b.absoluteString, "forward-address")
        let before = try await visit(view)
        reload.performClick(nil)
        try await wait { try await self.visit(view) > before && !view.isLoading }
        try require(reload.title == "Reload", "reload-refreshes-document")
        let slow = base.appendingPathComponent("slow")
        try submit(field, slow)
        try await wait {
            guard view.isLoading && view.url == slow && reload.title == "Stop"
                && field.stringValue == slow.absoluteString else { return false }
            let title = try? await view.callAsyncJavaScript("return document.title;", arguments: [:], in: nil, contentWorld: .page)
            return title as? String == "Navigation slow"
        }
        try require(window.subtitle == "Loading page", "loading-feedback")
        reload.performClick(nil)
        try await wait { !view.isLoading && reload.title == "Reload" }
        try require(window.subtitle == "Page load stopped.", "stop-feedback")
        try submit(field, base.appendingPathComponent("drop"))
        try await wait { !view.isLoading && !window.subtitle.isEmpty && window.subtitle != "Page load stopped." }
        try require(!window.subtitle.isEmpty, "network-error-feedback")
        try submit(field, a)
        try await wait { !view.isLoading && view.url == a && window.subtitle.isEmpty }
        try require(true, "navigation-after-error")
        try require(NSApp.windows.allSatisfy { !$0.isVisible }, "no-visible-test-window")
        finish()
    }

    private func finish(error: String? = nil) {
        guard !finished else { return }
        finished = true
        var roles: [String: Int32] = [:]
        if let page {
            let targets: [(String, NSObject, String)] = [
                ("content", page, "_webProcessIdentifier"), ("gpu", page, "_gpuProcessIdentifier"),
                ("network", page.configuration.websiteDataStore, "_networkProcessIdentifier")]
            for (role, receiver, name) in targets {
                let selector = NSSelectorFromString(name)
                guard let method = class_getInstanceMethod(type(of: receiver), selector),
                      method_getNumberOfArguments(method) == 2 else { continue }
                let kind = method_copyReturnType(method)
                defer { free(kind) }
                guard String(cString: kind) == "i" else { continue }
                typealias Getter = @convention(c) (AnyObject, Selector) -> Int32
                roles[role] = unsafeBitCast(method_getImplementation(method), to: Getter.self)(receiver, selector)
            }
        }
        var result: [String: Any] = ["passed": error == nil, "checks": checks, "pid": getpid(),
                                   "rolePIDs": roles, "rootRun": false,
                                   "scope": "Owner-driven navigation controls. No external-agent protection claim."]
        if let page { result["finalLoadingState"] = page.isLoading }
        if let error { result["error"] = error }
        if let data = try? JSONSerialization.data(withJSONObject: result, options: [.sortedKeys]),
           let line = String(data: data, encoding: .utf8) {
            print("BROWSER_NAVIGATION_RESULT " + line)
            fflush(stdout)
        }
        NSApp.terminate(nil)
    }
}

@main
private enum BrowserNavigationControl {
    @MainActor static func main() {
        guard getuid() != 0, geteuid() != 0, BrowserRuntimePolicy.disableDeveloperExtras() else { exit(64) }
        let app = NSApplication.shared
        let driver = NavigationDriver()
        app.setActivationPolicy(.prohibited)
        app.delegate = driver
        withExtendedLifetime(driver) { app.run() }
    }
}

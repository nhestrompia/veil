import AppKit
import WebKit
import Carbon
import Darwin

@MainActor
private final class FocusEngineDriver: NSObject, NSApplicationDelegate {
    private let browser = BrowserController()
    private var window: NSWindow?
    private var view: WKWebView?
    private var lastState = ""
    private let command: URL

    init(command: URL) { self.command = command }

    func applicationDidFinishLaunching(_ notification: Notification) {
        browser.applicationDidFinishLaunching(notification)
        guard let window = NSApp.windows.first, let content = window.contentView,
              let view = descendants(content).compactMap({ $0 as? WKWebView }).first else {
            NSApp.terminate(nil)
            return
        }
        self.window = window
        self.view = view
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        Task { @MainActor in
            do {
                try await Task.sleep(for: .milliseconds(400))
                key(49, " ")
                key(36, "\r")
                try await waitForPage()
                try await typeTask()
                print("FOCUS_CONTROL ready=true physicalHuman=false noDeviceReader=true")
                fflush(stdout)
                var lastCommand = 0
                for _ in 0..<900 {
                    reportState()
                    if let data = try? Data(contentsOf: command),
                       let value = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                       let number = value["id"] as? Int, number > lastCommand,
                       let operation = value["operation"] as? String {
                        lastCommand = number
                        if operation == "resume" {
                            try await typeTask()
                            print("FOCUS_CONTROL resumed=true")
                        } else if operation == "reload" {
                            view.reload()
                            try await waitForPage()
                            guard FocusEngineRuntime.reportContent(view) else { throw Failure.invalidContent }
                            try await typeTask()
                            print("FOCUS_CONTROL reloaded=true")
                        } else if operation == "stop" {
                            NSApp.terminate(nil)
                            return
                        } else {
                            throw Failure.invalidCommand
                        }
                        print("FOCUS_CONTROL commandCompleted=\(number) operation=\(operation)")
                        fflush(stdout)
                    }
                    try await Task.sleep(for: .milliseconds(100))
                }
            } catch {
                print("FOCUS_CONTROL failed=\(error)")
                fflush(stdout)
            }
            print("FOCUS_CONTROL deadlineOrFailure=true")
            fflush(stdout)
            NSApp.terminate(nil)
        }
    }

    private enum Failure: Error { case missingView, pageTimeout, invalidContent, invalidCommand }

    private func descendants(_ view: NSView) -> [NSView] { [view] + view.subviews.flatMap(descendants) }

    private func waitForPage() async throws {
        guard let view else { throw Failure.missingView }
        let deadline = ProcessInfo.processInfo.systemUptime + 8
        repeat {
            try await Task.sleep(for: .milliseconds(100))
            if !view.isLoading, (try? await view.evaluateJavaScript("typeof window.focusResearchField")) as? String == "function" {
                return
            }
        } while ProcessInfo.processInfo.systemUptime < deadline
        throw Failure.pageTimeout
    }

    private func typeTask() async throws {
        guard let view, let window else { throw Failure.missingView }
        window.makeFirstResponder(view)
        _ = try await view.evaluateJavaScript("window.focusResearchField()")
        try await Task.sleep(for: .milliseconds(150))
        let codes: [UInt16] = [45, 0, 17, 34, 9, 14, 27, 34, 45, 35, 32, 17, 36]
        for (code, character) in zip(codes, "native-input\r") {
            key(code, String(character))
            try await Task.sleep(for: .milliseconds(25))
        }
    }

    private func key(_ code: UInt16, _ text: String) {
        guard let window, let app = NSApp as? DeviceKeyboardApplication else { return }
        for down in [true, false] {
            guard let event = NSEvent.keyEvent(with: down ? .keyDown : .keyUp, location: .zero,
                modifierFlags: [], timestamp: ProcessInfo.processInfo.systemUptime,
                windowNumber: window.windowNumber, context: nil, characters: text,
                charactersIgnoringModifiers: text, isARepeat: false, keyCode: code) else { return }
            app.dispatchDeviceEvent(event)
        }
    }

    private func reportState() {
        guard let window else { return }
        let values: [String: Any] = ["keyWindow": window.isKeyWindow, "visible": window.isVisible,
            "active": NSApp.isActive, "foreground": NSWorkspace.shared.frontmostApplication?.processIdentifier == getpid(),
            "viewSecureOwner": DiagnosticSecureInput.owner(in: window.contentView),
            "aggregateSecureInput": IsSecureEventInputEnabled()]
        guard let data = try? JSONSerialization.data(withJSONObject: values, options: .sortedKeys),
              let state = String(data: data, encoding: .utf8), state != lastState else { return }
        lastState = state
        print("FOCUS_CONTROL_STATE " + state)
        fflush(stdout)
    }

    func applicationDidBecomeActive(_ notification: Notification) { browser.applicationDidBecomeActive(notification) }
    func applicationWillResignActive(_ notification: Notification) { browser.applicationWillResignActive(notification) }
    func applicationWillTerminate(_ notification: Notification) { browser.applicationWillTerminate(notification) }
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }
}

@main
private enum FocusEngineControl {
    @MainActor static func main() {
        alarm(120)
        let args = CommandLine.arguments
        guard getuid() != 0, geteuid() != 0, args.count == 5, args[1] == "--url", args[3] == "--command",
              let url = URL(string: args[2]), url.scheme == "http", url.host == "127.0.0.1",
              url.port.map({ (1024...65535).contains($0) }) == true, url.user == nil, url.password == nil,
              url.path.range(of: "\\A/trial/[0-9a-f]{16}\\z", options: .regularExpression) != nil,
              BrowserRuntimePolicy.disableDeveloperExtras(), FocusEngineRuntime.preflight() else { exit(64) }
        let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
            .deletingLastPathComponent().deletingLastPathComponent().appendingPathComponent("artifacts").path + "/"
        let command = URL(fileURLWithPath: args[4]).resolvingSymlinksInPath()
        guard command.path.hasPrefix(root) else { exit(64) }
        let app = DeviceKeyboardApplication.shared
        app.setActivationPolicy(.regular)
        let driver = FocusEngineDriver(command: command)
        app.delegate = driver
        withExtendedLifetime(driver) { app.run() }
    }
}

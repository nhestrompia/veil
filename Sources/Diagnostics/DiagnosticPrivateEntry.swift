import AppKit
import Carbon

@MainActor
final class DiagnosticPrivateEntry: NSObject {
    private weak var window: NSWindow?
    private var policy = PrivateEntryPolicy()
    private var ownsProtection = false
    private var expiry: Task<Void, Never>?

    init(window: NSWindow) {
        self.window = window
        super.init()
        for name in [NSWindow.didResignKeyNotification, NSWindow.didMiniaturizeNotification, NSWindow.willCloseNotification] {
            NotificationCenter.default.addObserver(self, selector: #selector(focusLost), name: name, object: window)
        }
        for name in [NSApplication.willResignActiveNotification, NSApplication.didHideNotification, NSApplication.willTerminateNotification] {
            NotificationCenter.default.addObserver(self, selector: #selector(focusLost), name: name, object: NSApp)
        }
    }

    private var focus: PrivateEntryFocus {
        PrivateEntryFocus(active: NSApp.isActive, key: window?.isKeyWindow == true,
                          visible: window?.isVisible == true, miniaturized: window?.isMiniaturized != false,
                          foreground: NSWorkspace.shared.frontmostApplication?.processIdentifier == getpid())
    }

    func begin() -> Bool {
        end(reason: "replace-session")
        guard focus.eligible, policy.begin(now: ProcessInfo.processInfo.systemUptime, seconds: 10) else {
            print("PRIVATE_ENTRY began=false reason=native-focus")
            return false
        }
        let result = EnableSecureEventInput()
        ownsProtection = result == noErr
        guard ownsProtection, IsSecureEventInputEnabled() else {
            end(reason: "acquisition-failed")
            print("PRIVATE_ENTRY began=false reason=acquisition")
            return false
        }
        expiry = Task { @MainActor [weak self] in
            do { try await Task.sleep(for: .seconds(10)) } catch { return }
            self?.end(reason: "expiry")
        }
        print("PRIVATE_ENTRY began=true maximumSeconds=10")
        fflush(stdout)
        return true
    }

    func permitsInput() -> Bool {
        guard policy.permits(now: ProcessInfo.processInfo.systemUptime, focus: focus),
              ownsProtection, IsSecureEventInputEnabled() else {
            end(reason: "input-ineligible")
            return false
        }
        return true
    }

    func end(reason: String) {
        expiry?.cancel()
        expiry = nil
        policy.end()
        if ownsProtection {
            let result = DisableSecureEventInput()
            ownsProtection = false
            print("PRIVATE_ENTRY ended=true reason=\(reason) releaseStatus=\(result) secureInput=\(IsSecureEventInputEnabled())")
            fflush(stdout)
        }
    }

    @objc private func focusLost(_ notification: Notification) {
        end(reason: "native-focus-loss")
    }
}

import AppKit
import ApplicationServices

@MainActor
final class KeyboardObservationProbe {
    private let target: NSRunningApplication
    private let expected = Array("native-input")
    private var prefix: [Character] = []
    private var eventCount = 0
    private var unownedEventCount = 0
    private var phraseMatched = false
    private var monitor: Any?
    private var timer: Timer?
    private let deadline = Date().addingTimeInterval(15)

    init(target: NSRunningApplication) { self.target = target }

    func report(status: String, reason: String) {
        let result: [String: Any] = [
            "status": status, "reason": reason, "targetPID": target.processIdentifier,
            "accessibility": AXIsProcessTrusted(), "listenEvents": CGPreflightListenEventAccess(),
            "eventCount": eventCount, "expectedFakePhraseMatched": phraseMatched,
            "unownedEventCount": unownedEventCount,
            "monitorRemoved": monitor == nil, "rawTextSaved": false, "keyCodesSaved": false,
            "method": "Passive NSEvent global monitor; exact foreground research PID; 15-second maximum"
        ]
        if let data = try? JSONSerialization.data(withJSONObject: result, options: [.prettyPrinted, .sortedKeys]) {
            print(String(decoding: data, as: UTF8.self))
        }
    }

    func finish(reason: String) {
        if let monitor { NSEvent.removeMonitor(monitor) }
        monitor = nil
        timer?.invalidate()
        timer = nil
        report(status: "observation-finished", reason: reason)
        exit(0)
    }

    private func ownsFocus() -> Bool {
        !target.isTerminated && NSWorkspace.shared.frontmostApplication?.processIdentifier == target.processIdentifier
    }

    private func ownsEvent(_ event: NSEvent) -> Bool {
        guard event.windowNumber > 0,
              let windows = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] else { return false }
        return windows.contains { window in
            (window[kCGWindowOwnerPID as String] as? Int32) == target.processIdentifier
                && (window[kCGWindowNumber as String] as? Int) == event.windowNumber
        }
    }

    func start() {
        guard AXIsProcessTrusted() else {
            report(status: "inconclusive", reason: "No effective Accessibility grant. No monitor installed or permission requested.")
            return
        }
        guard ownsFocus() else {
            report(status: "inconclusive", reason: "Research target is not frontmost. No monitor installed.")
            return
        }
        monitor = NSEvent.addGlobalMonitorForEvents(matching: .keyDown) { [weak self] event in
            MainActor.assumeIsolated {
                guard let self else { return }
                // Check ownership before extracting any key text.
                guard self.ownsFocus(), Date() < self.deadline else {
                    self.finish(reason: "Target lost focus or deadline reached")
                    return
                }
                guard self.ownsEvent(event) else {
                    self.unownedEventCount += 1
                    return
                }
                self.eventCount += 1
                for character in event.characters ?? "" {
                    self.prefix.append(character)
                    while !self.expected.starts(with: self.prefix) { self.prefix.removeFirst() }
                    if self.prefix == self.expected {
                        self.phraseMatched = true
                        self.prefix.removeAll(keepingCapacity: false)
                    }
                }
            }
        }
        guard monitor != nil else {
            report(status: "inconclusive", reason: "AppKit did not create the passive monitor")
            return
        }
        timer = Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { [weak self] _ in
            MainActor.assumeIsolated {
                guard let self else { return }
                if !self.ownsFocus() || Date() >= self.deadline { self.finish(reason: "Focus loss or timeout") }
            }
        }
        NSApplication.shared.run()
    }
}

@main
struct KeyboardObservationMain {
    @MainActor static func main() {
        let args = CommandLine.arguments
        guard args.count == 3, ["preflight", "observe"].contains(args[1]), let pid = Int32(args[2]),
              let target = NSRunningApplication(processIdentifier: pid),
              ["research.agentfreebrowser.devicekeyboard", "research.agentfreebrowser.control"].contains(target.bundleIdentifier ?? "") else {
            fputs("Use preflight|observe with an exact running research browser PID\n", stderr)
            exit(2)
        }
        let observer = KeyboardObservationProbe(target: target)
        if args[1] == "preflight" {
            observer.report(status: "preflight-only", reason: "No monitor installed or permission requested")
        } else {
            observer.start()
        }
    }
}

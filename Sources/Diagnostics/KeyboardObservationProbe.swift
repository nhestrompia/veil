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
    private var keyMatcher = FakeKeyMatcher()
    private var eventsWithUnicode = 0
    private var monitor: Any?
    private var tap: CFMachPort?
    private var tapSource: CFRunLoopSource?
    private var method = "Passive NSEvent global monitor; exact foreground research PID; 15-second maximum"
    private var timer: Timer?
    private let deadline = Date().addingTimeInterval(15)

    init(target: NSRunningApplication) { self.target = target }

    func report(status: String, reason: String) {
        let result: [String: Any] = [
            "status": status, "reason": reason, "targetPID": target.processIdentifier,
            "accessibility": AXIsProcessTrusted(), "listenEvents": CGPreflightListenEventAccess(),
            "eventCount": eventCount, "expectedFakePhraseMatched": phraseMatched,
            "expectedFakeKeycodeSequenceMatched": keyMatcher.matched, "eventsWithUnicode": eventsWithUnicode,
            "unownedEventCount": unownedEventCount,
            "monitorRemoved": monitor == nil && tap == nil, "rawTextSaved": false, "keyCodesSaved": false,
            "method": method
        ]
        if let data = try? JSONSerialization.data(withJSONObject: result, options: [.prettyPrinted, .sortedKeys]) {
            print(String(decoding: data, as: UTF8.self))
        }
    }

    func finish(reason: String) {
        if let monitor { NSEvent.removeMonitor(monitor) }
        monitor = nil
        if let tap { CFMachPortInvalidate(tap) }
        if let tapSource { CFRunLoopRemoveSource(CFRunLoopGetMain(), tapSource, .commonModes) }
        tap = nil
        tapSource = nil
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

    private func match(_ text: String) {
        for character in text {
            prefix.append(character)
            while !expected.starts(with: prefix) { prefix.removeFirst() }
            if prefix == expected {
                phraseMatched = true
                prefix.removeAll(keepingCapacity: false)
            }
        }
    }

    private func receivePIDEvent(type: CGEventType, event: CGEvent) {
        guard ownsFocus(), Date() < deadline else {
            finish(reason: "Target lost focus or deadline reached")
            return
        }
        guard type == .keyDown else {
            finish(reason: "PID tap delivered an unexpected event type")
            return
        }
        eventCount += 1
        keyMatcher.consume(event.getIntegerValueField(.keyboardEventKeycode))
        var units = [UniChar](repeating: 0, count: 16)
        var length = 0
        event.keyboardGetUnicodeString(maxStringLength: units.count, actualStringLength: &length, unicodeString: &units)
        if length > 0 { eventsWithUnicode += 1 }
        match(String(decoding: units.prefix(min(length, units.count)), as: UTF16.self))
    }

    private func runUntilDeadline() {
        timer = Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { [weak self] _ in
            MainActor.assumeIsolated {
                guard let self else { return }
                if !self.ownsFocus() || Date() >= self.deadline { self.finish(reason: "Focus loss or timeout") }
            }
        }
        NSApplication.shared.run()
    }

    func startPIDTap() {
        method = "CGEvent tapCreateForPid; listenOnly; keyDown only; exact foreground research PID; 15-second maximum"
        guard CGPreflightListenEventAccess(), ownsFocus() else {
            report(status: "inconclusive", reason: "Listening access or foreground target unavailable. No tap installed.")
            return
        }
        let callback: CGEventTapCallBack = { _, type, event, context in
            if let context {
                MainActor.assumeIsolated {
                    Unmanaged<KeyboardObservationProbe>.fromOpaque(context).takeUnretainedValue().receivePIDEvent(type: type, event: event)
                }
            }
            return Unmanaged.passUnretained(event)
        }
        tap = CGEvent.tapCreateForPid(pid: target.processIdentifier, place: .tailAppendEventTap,
                                     options: .listenOnly, eventsOfInterest: CGEventMask(1) << CGEventType.keyDown.rawValue,
                                     callback: callback, userInfo: Unmanaged.passUnretained(self).toOpaque())
        guard let tap, let source = CFMachPortCreateRunLoopSource(kCFAllocatorDefault, tap, 0) else {
            if let tap { CFMachPortInvalidate(tap) }
            tap = nil
            report(status: "inconclusive", reason: "PID-scoped passive tap or run-loop source unavailable")
            return
        }
        tapSource = source
        CFRunLoopAddSource(CFRunLoopGetMain(), source, .commonModes)
        runUntilDeadline()
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
                self.match(event.characters ?? "")
            }
        }
        guard monitor != nil else {
            report(status: "inconclusive", reason: "AppKit did not create the passive monitor")
            return
        }
        runUntilDeadline()
    }
}

@main
struct KeyboardObservationMain {
    @MainActor static func main() {
        let args = CommandLine.arguments
        guard args.count == 3, ["preflight", "observe", "observe-pid"].contains(args[1]), let pid = Int32(args[2]),
              let target = NSRunningApplication(processIdentifier: pid),
              ["research.agentfreebrowser.devicekeyboard", "research.agentfreebrowser.control"].contains(target.bundleIdentifier ?? "") else {
            fputs("Use preflight|observe|observe-pid with an exact running research browser PID\n", stderr)
            exit(2)
        }
        let observer = KeyboardObservationProbe(target: target)
        if args[1] == "preflight" {
            observer.report(status: "preflight-only", reason: "No monitor installed or permission requested")
        } else if args[1] == "observe-pid" {
            observer.startPIDTap()
        } else {
            observer.start()
        }
    }
}

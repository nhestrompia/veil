import AppKit

@MainActor
func dragResearchPayload(target: NSRunningApplication, source: NSRunningApplication, point: CGPoint) async throws {
    guard source.bundleIdentifier == "research.agentfreebrowser.dragsource",
          target.processIdentifier != source.processIdentifier,
          CGPreflightPostEventAccess() else { throw ProbeFailure("Research drag source or event permission is invalid") }
    let sourcePID = source.processIdentifier, targetPID = target.processIdentifier
    let owners = Set([sourcePID, targetPID])
    func checkedWindows() throws -> [[String: Any]] {
        guard let front = NSWorkspace.shared.frontmostApplication?.processIdentifier, owners.contains(front) else {
            throw ProbeFailure("Research drag lost foreground ownership")
        }
        return CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] ?? []
    }
    func checkPoint(_ location: CGPoint, windows: [[String: Any]]) throws {
        for window in windows {
            if (window[kCGWindowLayer as String] as? Int) == Int(CGWindowLevelForKey(.cursorWindow)) { continue }
            guard (window[kCGWindowAlpha as String] as? Double ?? 1) > 0,
                  let frame = frameOfWindow(window), frame.contains(location) else { continue }
            guard let owner = window[kCGWindowOwnerPID as String] as? Int32, owners.contains(owner) else {
                throw ProbeFailure("A non-research window covers the drag path")
            }
            return
        }
        throw ProbeFailure("No owned research window covers the drag point")
    }
    source.activate(options: [])
    try await Task.sleep(for: .milliseconds(300))
    let windows = try checkedWindows()
    guard let sourceWindow = windows.first(where: { ($0[kCGWindowOwnerPID as String] as? Int32) == sourcePID }),
          let sourceFrame = frameOfWindow(sourceWindow),
          let targetWindow = windows.first(where: {
              ($0[kCGWindowOwnerPID as String] as? Int32) == targetPID && ($0[kCGWindowLayer as String] as? Int) == 0
          }), let targetFrame = frameOfWindow(targetWindow),
          targetFrame.contains(sourceFrame), targetFrame.insetBy(dx: 10, dy: 40).contains(point),
          !sourceFrame.contains(point) else { throw ProbeFailure("Drag endpoints must lie inside the research target") }
    let start = CGPoint(x: sourceFrame.midX, y: sourceFrame.midY)
    let eventSource = CGEventSource(stateID: .hidSystemState)
    var pressed = false
    func send(_ type: CGEventType, at location: CGPoint) throws {
        try checkPoint(location, windows: checkedWindows())
        guard let event = CGEvent(mouseEventSource: eventSource, mouseType: type, mouseCursorPosition: location, mouseButton: .left) else {
            throw ProbeFailure("Cannot construct research drag event")
        }
        event.post(tap: .cghidEventTap)
    }
    do {
        try send(.mouseMoved, at: start)
        try await Task.sleep(for: .milliseconds(80))
        try send(.leftMouseDown, at: start)
        pressed = true
        try await Task.sleep(for: .milliseconds(150))
        for step in 1...40 {
            let t = Double(step) / 40
            let location = CGPoint(x: start.x + (point.x - start.x) * t, y: start.y + (point.y - start.y) * t)
            guard targetFrame.contains(location) else { throw ProbeFailure("Research drag left the target frame") }
            try send(.leftMouseDragged, at: location)
            try await Task.sleep(for: .milliseconds(20))
        }
        try await Task.sleep(for: .milliseconds(300))
        try send(.leftMouseUp, at: point)
        pressed = false
        try emit(["status": "attempted", "pid": targetPID, "sourcePID": sourcePID,
                  "source": [start.x, start.y], "destination": [point.x, point.y],
                  "scope": "Fixed disposable text through an AppKit dragging session. No general clipboard access."])
    } catch {
        if pressed { try? send(.leftMouseUp, at: start) }
        throw error
    }
}

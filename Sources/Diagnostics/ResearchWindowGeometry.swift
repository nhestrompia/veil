import AppKit
import CoreGraphics

private enum GeometryFailure: Error {
    case invalidArguments
    case unrelatedTarget
    case permissionUnavailable
    case windowUnavailable
    case ownershipChanged
    case pointCovered
    case eventUnavailable
}

@main
@MainActor
enum ResearchWindowGeometry {
    private static let root = URL(fileURLWithPath: #filePath)
        .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
        .resolvingSymlinksInPath().path

    private static func emit(_ value: [String: Any]) throws {
        let data = try JSONSerialization.data(withJSONObject: value, options: [.sortedKeys])
        FileHandle.standardOutput.write(data)
        FileHandle.standardOutput.write(Data([10]))
    }

    private static func bounds(_ window: [String: Any]) -> CGRect? {
        guard let raw = window[kCGWindowBounds as String] as? [String: Any] else { return nil }
        return CGRect(dictionaryRepresentation: raw as CFDictionary)
    }

    private static func windows() -> [[String: Any]] {
        CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] ?? []
    }

    private static func post(_ pid: Int32, operation: GeometryOperation) async throws {
        let identity = try ResearchProcessIdentity(pid: pid)
        guard WindowGeometryScope.permits(root: root, pid: pid, path: identity.path),
              let app = NSRunningApplication(processIdentifier: pid),
              ["research.agentfreebrowser.control", "research.agentfreebrowser.internalkeyboardcontrol"].contains(app.bundleIdentifier ?? "") else {
            throw GeometryFailure.unrelatedTarget
        }
        guard CGPreflightPostEventAccess() else { throw GeometryFailure.permissionUnavailable }
        try DesktopInputSafety.observe().requireIsolatedMouse()
        app.activate(options: [])
        try await Task.sleep(for: .milliseconds(300))
        guard let window = windows().first(where: { ($0[kCGWindowOwnerPID as String] as? Int32) == pid
            && ($0[kCGWindowLayer as String] as? Int) == 0 }),
              let frame = bounds(window), let id = window[kCGWindowNumber as String] as? UInt32,
              let (start, end) = WindowGeometryScope.points(frame: frame, operation: operation) else {
            throw GeometryFailure.windowUnavailable
        }
        let source = CGEventSource(stateID: .hidSystemState)
        var pressed = false
        defer {
            if pressed {
                let location = CGEvent(source: nil)?.location ?? start
                CGEvent(mouseEventSource: source, mouseType: .leftMouseUp, mouseCursorPosition: location, mouseButton: .left)?.post(tap: .cghidEventTap)
            }
        }
        func send(_ type: CGEventType, point: CGPoint) throws {
            guard try ResearchProcessIdentity(pid: pid) == identity,
                  NSWorkspace.shared.frontmostApplication?.processIdentifier == pid else { throw GeometryFailure.ownershipChanged }
            try DesktopInputSafety.observe().requireIsolatedMouse()
            guard frame.contains(point) else { throw GeometryFailure.pointCovered }
            let covering = windows().first { window in
                guard (window[kCGWindowLayer as String] as? Int) != Int(CGWindowLevelForKey(.cursorWindow)),
                      (window[kCGWindowAlpha as String] as? Double ?? 1) > 0, let box = bounds(window) else { return false }
                return box.contains(point)
            }
            guard covering?[kCGWindowOwnerPID as String] as? Int32 == pid,
                  covering?[kCGWindowNumber as String] as? UInt32 == id else { throw GeometryFailure.pointCovered }
            guard let event = CGEvent(mouseEventSource: source, mouseType: type, mouseCursorPosition: point, mouseButton: .left) else {
                throw GeometryFailure.eventUnavailable
            }
            event.post(tap: .cghidEventTap)
        }
        try send(.mouseMoved, point: start)
        try await Task.sleep(for: .milliseconds(80))
        try send(.leftMouseDown, point: start)
        pressed = true
        try await Task.sleep(for: .milliseconds(120))
        for step in 1...24 {
            let t = Double(step) / 24
            try send(.leftMouseDragged, point: CGPoint(x: start.x + (end.x - start.x) * t, y: start.y + (end.y - start.y) * t))
            try await Task.sleep(for: .milliseconds(25))
        }
        try send(.leftMouseUp, point: end)
        pressed = false
        try await Task.sleep(for: .milliseconds(250))
        let after = windows().first { ($0[kCGWindowNumber as String] as? UInt32) == id }.flatMap(bounds)
        try emit(["status": "attempted", "pid": pid, "operation": operation.rawValue,
                  "beforeFrame": [frame.minX, frame.minY, frame.width, frame.height],
                  "afterFrame": after.map { [$0.minX, $0.minY, $0.width, $0.height] } as Any? ?? NSNull(),
                  "noKeyboardInput": true])
    }

    static func main() async {
        do {
            let args = Array(CommandLine.arguments.dropFirst())
            if args == ["--preflight"] {
                try emit(["postEvents": CGPreflightPostEventAccess(), "desktopInputSafety": DesktopInputSafety.observe().report,
                          "permissionRequested": false, "inputPosted": false])
            } else if args == ["--request-post-events"] {
                let granted = CGRequestPostEventAccess()
                try emit(["postEvents": granted, "permissionRequested": true, "inputPosted": false])
            } else if args.count == 2, let operation = GeometryOperation(rawValue: args[0]), let pid = Int32(args[1]), pid > 1 {
                try await post(pid, operation: operation)
            } else { throw GeometryFailure.invalidArguments }
        } catch {
            try? emit(["status": "refused-or-failed", "error": String(describing: error)])
            exit(1)
        }
    }
}

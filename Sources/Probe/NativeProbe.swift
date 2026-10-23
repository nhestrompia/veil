import AppKit
import ApplicationServices
import ScreenCaptureKit
import ImageIO
import UniformTypeIdentifiers
import Vision
import IOKit.hidsystem

struct ProbeFailure: Error, CustomStringConvertible {
    let description: String
    init(_ description: String) { self.description = description }
}

func emit(_ value: [String: Any]) throws {
    let data = try JSONSerialization.data(withJSONObject: value, options: [.prettyPrinted, .sortedKeys])
    if let index = CommandLine.arguments.firstIndex(of: "--out"), CommandLine.arguments.indices.contains(index + 1) {
        try data.write(to: URL(fileURLWithPath: CommandLine.arguments[index + 1]), options: .atomic)
    }
    print(String(decoding: data, as: UTF8.self))
}

func attribute(_ element: AXUIElement, _ name: String) -> CFTypeRef? {
    var value: CFTypeRef?
    guard AXUIElementCopyAttributeValue(element, name as CFString, &value) == .success else { return nil }
    return value
}

func elements(_ root: AXUIElement) -> [AXUIElement] {
    var result: [AXUIElement] = []
    var visited: Set<AXUIElement> = []
    var pending: [(AXUIElement, Int)] = [(root, 0)]
    while let (element, depth) = pending.popLast(), result.count < 3000 {
        guard visited.insert(element).inserted else { continue }
        // System menus contain unrelated recent documents and can link back to the application.
        if (attribute(element, kAXRoleAttribute) as? String) == kAXMenuBarRole { continue }
        result.append(element)
        if depth < 35 {
            for key in [kAXChildrenAttribute, kAXWindowsAttribute] {
                if let children = attribute(element, key) as? [AXUIElement] {
                    pending.append(contentsOf: children.reversed().map { ($0, depth + 1) })
                }
            }
            for key in [kAXFocusedWindowAttribute, kAXFocusedUIElementAttribute] {
                if let raw = attribute(element, key), CFGetTypeID(raw) == AXUIElementGetTypeID() {
                    pending.append((raw as! AXUIElement, depth + 1))
                }
            }
        }
    }
    return result
}

func description(_ element: AXUIElement) -> [String: Any] {
    var result: [String: Any] = [:]
    for key in [kAXRoleAttribute, kAXTitleAttribute, kAXDescriptionAttribute, kAXValueAttribute] {
        if let text = attribute(element, key) as? String { result[key] = text }
    }
    var names: CFArray?
    if AXUIElementCopyActionNames(element, &names) == .success { result["actions"] = names as? [String] ?? [] }
    for key in [kAXPositionAttribute, kAXSizeAttribute] {
        guard let raw = attribute(element, key), CFGetTypeID(raw) == AXValueGetTypeID() else { continue }
        // The type ID check establishes the CF subtype before extraction.
        let value = raw as! AXValue
        if key == kAXPositionAttribute {
            var point = CGPoint.zero
            if AXValueGetValue(value, .cgPoint, &point) { result["position"] = [point.x, point.y] }
        } else {
            var size = CGSize.zero
            if AXValueGetValue(value, .cgSize, &size) { result["size"] = [size.width, size.height] }
        }
    }
    return result
}

func target(_ value: String) throws -> NSRunningApplication {
    guard let pid = pid_t(value), let app = NSRunningApplication(processIdentifier: pid),
          let bundle = app.bundleIdentifier,
          bundle.hasPrefix("research.agentfreebrowser.") else {
        throw ProbeFailure("Target must be a running research browser bundle")
    }
    return app
}

@MainActor
func post(_ event: CGEvent, pid: pid_t?, targetPID: pid_t) throws {
    if let pid {
        event.postToPid(pid)
    } else {
        guard NSWorkspace.shared.frontmostApplication?.processIdentifier == targetPID else {
            throw ProbeFailure("Target lost foreground focus; refusing further global input")
        }
        event.post(tap: .cghidEventTap)
    }
}

@MainActor
func sendKey(_ code: CGKeyCode, flags: CGEventFlags = [], pid: pid_t? = nil, source: CGEventSource?, targetPID: pid_t) throws {
    for down in [true, false] {
        guard let event = CGEvent(keyboardEventSource: source, virtualKey: code, keyDown: down) else {
            throw ProbeFailure("Cannot construct keyboard event")
        }
        event.flags = down ? flags : []
        try post(event, pid: pid, targetPID: targetPID)
        Thread.sleep(forTimeInterval: 0.03)
    }
}

@MainActor
func typeText(_ text: String, pid: pid_t? = nil, source: CGEventSource?, targetPID: pid_t) throws {
    for character in text.utf16 {
        var unit = character
        for down in [true, false] {
            guard let event = CGEvent(keyboardEventSource: source, virtualKey: 0, keyDown: down) else {
                throw ProbeFailure("Cannot construct text event")
            }
            event.keyboardSetUnicodeString(stringLength: 1, unicodeString: &unit)
            event.flags = []
            try post(event, pid: pid, targetPID: targetPID)
        }
        Thread.sleep(forTimeInterval: 0.04)
    }
}

@MainActor
func click(_ point: CGPoint, pid: pid_t? = nil, source: CGEventSource?, targetPID: pid_t) throws {
    for type in [CGEventType.mouseMoved, .leftMouseDown, .leftMouseUp] {
        guard let event = CGEvent(mouseEventSource: source, mouseType: type, mouseCursorPosition: point, mouseButton: .left) else {
            throw ProbeFailure("Cannot construct mouse event")
        }
        try post(event, pid: pid, targetPID: targetPID)
        Thread.sleep(forTimeInterval: 0.08)
    }
}

@main
enum NativeProbe {
    @MainActor static func main() async {
        _ = NSApplication.shared
        var arguments = Array(CommandLine.arguments.dropFirst())
        if let index = arguments.firstIndex(of: "--out"), arguments.indices.contains(index + 1) {
            arguments.removeSubrange(index...index + 1)
        }
        do { try await run(arguments) }
        catch {
            try? emit(["status": "inconclusive", "error": String(describing: error)])
            exit(2)
        }
    }

    @MainActor static func run(_ args: [String]) async throws {
        guard let command = args.first else { throw ProbeFailure("Use permissions, windows, ax, ax-action, input, capture, or ocr") }
        if command == "permissions" {
            try emit(["pid": getpid(), "accessibility": AXIsProcessTrusted(),
                      "postEvents": CGPreflightPostEventAccess(), "screenCapture": CGPreflightScreenCaptureAccess()])
            return
        }
        if command == "request-permissions" {
            let accessibility = AXIsProcessTrusted()
            let postEvents = CGRequestPostEventAccess()
            let screenCapture = CGRequestScreenCaptureAccess()
            try emit(["accessibility": accessibility, "postEvents": postEvents, "screenCapture": screenCapture])
            return
        }
        if command == "ocr" {
            guard args.count == 2 else { throw ProbeFailure("ocr PNG") }
            let request = VNRecognizeTextRequest()
            request.recognitionLevel = .accurate
            try VNImageRequestHandler(url: URL(fileURLWithPath: args[1])).perform([request])
            try emit(["text": (request.results ?? []).compactMap { observation -> [String: Any]? in
                guard let text = observation.topCandidates(1).first else { return nil }
                let box = observation.boundingBox
                return ["text": text.string, "confidence": text.confidence,
                        "box": [box.minX, box.minY, box.width, box.height]]
            }])
            return
        }
        guard args.count >= 2 else { throw ProbeFailure("Missing target PID") }
        let app = try target(args[1])
        let pid = app.processIdentifier
        if command == "windows" {
            let list = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] ?? []
            try emit(["windows": list.filter { ($0[kCGWindowOwnerPID as String] as? Int32) == pid }])
            return
        }
        if command == "ax" || command == "ax-action" {
            guard AXIsProcessTrusted() else { throw ProbeFailure("Accessibility permission is absent for this probe process") }
            let tree = elements(AXUIElementCreateApplication(pid))
            if command == "ax" {
                try emit(["status": "observed", "pid": pid, "elements": tree.map(description)])
                return
            }
            guard let field = tree.first(where: {
                (attribute($0, kAXRoleAttribute) as? String) == kAXTextFieldRole &&
                ((attribute($0, kAXDescriptionAttribute) as? String) == "Enter native-input" ||
                 (attribute($0, kAXTitleAttribute) as? String) == "Enter native-input")
            }), let button = tree.first(where: {
                (attribute($0, kAXRoleAttribute) as? String) == kAXButtonRole &&
                ((attribute($0, kAXTitleAttribute) as? String) == "Record action" ||
                 (attribute($0, kAXDescriptionAttribute) as? String) == "Record action")
            }) else { throw ProbeFailure("Fixture field or action not found in AX tree") }
            app.activate(options: [])
            try await Task.sleep(for: .milliseconds(300))
            let focusResult = AXUIElementSetAttributeValue(field, kAXFocusedAttribute as CFString, kCFBooleanTrue)
            try await Task.sleep(for: .milliseconds(150))
            let valueResult = AXUIElementSetAttributeValue(field, kAXValueAttribute as CFString, "native-input" as CFString)
            try await Task.sleep(for: .milliseconds(150))
            let pressResult = AXUIElementPerformAction(button, kAXPressAction as CFString)
            try emit(["status": "attempted", "pid": pid, "focusError": focusResult.rawValue,
                      "setValueError": valueResult.rawValue, "pressError": pressResult.rawValue])
            return
        }
        if command == "input" {
            guard args.count >= 5, let x = Double(args[2]), let y = Double(args[3]) else {
                throw ProbeFailure("input PID X Y session|hid|private [pid]")
            }
            guard CGPreflightPostEventAccess() else { throw ProbeFailure("Event-posting permission is absent for this probe process") }
            let sourceID: CGEventSourceStateID
            switch args[4] {
            case "session": sourceID = .combinedSessionState
            case "hid": sourceID = .hidSystemState
            case "private": sourceID = .privateState
            default: throw ProbeFailure("Unknown event source")
            }
            let source = CGEventSource(stateID: sourceID)
            let directed = args.contains("pid") ? pid : nil
            app.activate(options: [])
            try await Task.sleep(for: .milliseconds(300))
            guard directed != nil || NSWorkspace.shared.frontmostApplication?.processIdentifier == pid else {
                throw ProbeFailure("Target is not frontmost; refusing global input")
            }
            if args.contains("curve") {
                let start = CGPoint(x: max(110, x - 190), y: max(190, y - 110))
                let bend = CGFloat.random(in: -75...75)
                for step in 0...60 {
                    let t = CGFloat(step) / 60
                    let eased = t * t * (3 - 2 * t)
                    let point = CGPoint(x: start.x + (x - start.x) * eased,
                                        y: start.y + (y - start.y) * eased + sin(t * .pi) * bend)
                    guard let event = CGEvent(mouseEventSource: source, mouseType: .mouseMoved,
                                              mouseCursorPosition: point, mouseButton: .left) else {
                        throw ProbeFailure("Cannot construct trajectory event")
                    }
                    try post(event, pid: directed, targetPID: pid)
                    try await Task.sleep(for: .milliseconds(Int.random(in: 8...20)))
                }
            }
            try click(CGPoint(x: x, y: y), pid: directed, source: source, targetPID: pid)
            if args.contains("keycodes") {
                for code: CGKeyCode in [45, 0, 17, 34, 9, 14, 27, 34, 45, 35, 32, 17] {
                    try sendKey(code, pid: directed, source: source, targetPID: pid)
                }
            } else {
                try typeText("native-input", pid: directed, source: source, targetPID: pid)
            }
            try sendKey(36, pid: directed, source: source, targetPID: pid)
            try emit(["status": "attempted", "pid": pid, "source": args[4],
                      "directToPID": directed != nil, "curvedTrajectory": args.contains("curve")])
            return
        }
        if command == "hid-post-input" {
            guard args.count == 5, let x = Double(args[2]), let y = Double(args[3]),
                  ["legacy", "reports"].contains(args[4]) else {
                throw ProbeFailure("hid-post-input PID X Y legacy|reports")
            }
            guard IOHIDCheckAccess(kIOHIDRequestTypePostEvent) == kIOHIDAccessTypeGranted else {
                throw ProbeFailure("The probe requires its approved event-posting grant")
            }
            var connection: UInt32 = 0
            let openResult = AFBOpenHIDPosting(&connection)
            guard openResult == 0 else {
                try emit(["status": "inconclusive", "openResult": openResult, "route": args[4]])
                return
            }
            defer { AFBCloseHIDPosting(connection) }
            app.activate(options: [])
            try await Task.sleep(for: .milliseconds(300))
            let source = CGEventSource(stateID: .hidSystemState)
            try click(CGPoint(x: x, y: y), source: source, targetPID: pid)
            let codes: [UInt16] = [45, 0, 17, 34, 9, 14, 27, 34, 45, 35, 32, 17, 36]
            let characters = Array("native-input\r".utf16)
            var statuses: [Int32] = []
            for (code, character) in zip(codes, characters) {
                for down: Int32 in [1, 0] {
                    guard NSWorkspace.shared.frontmostApplication?.processIdentifier == pid else {
                        throw ProbeFailure("Target lost foreground focus; refusing HID posting")
                    }
                    statuses.append(AFBPostHIDKey(connection, code, character, down, args[4] == "reports" ? 1 : 0))
                    try await Task.sleep(for: .milliseconds(35))
                }
            }
            try emit(["status": "attempted", "route": args[4], "openResult": openResult,
                      "postResults": statuses, "fieldFocusSource": "CGEvent click; typing uses IOHIDPostEvent"])
            return
        }
        if command == "system-capture" {
            guard args.count == 3 else { throw ProbeFailure("system-capture PID OUTPUT.png") }
            guard CGPreflightScreenCaptureAccess() else { throw ProbeFailure("Screen Recording permission is absent for this probe process") }
            let list = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] ?? []
            guard let window = list.first(where: { ($0[kCGWindowOwnerPID as String] as? Int32) == pid && ($0[kCGWindowLayer as String] as? Int) == 0 }),
                  let number = window[kCGWindowNumber as String] as? Int else {
                throw ProbeFailure("No visible target window")
            }
            let capture = Process()
            capture.executableURL = URL(fileURLWithPath: "/usr/sbin/screencapture")
            capture.arguments = ["-x", "-l", String(number), args[2]]
            try capture.run()
            capture.waitUntilExit()
            guard capture.terminationStatus == 0 else { throw ProbeFailure("System capture failed") }
            try emit(["status": "captured", "pid": pid, "windowID": number, "path": args[2]])
            return
        }
        if command == "capture" || command == "display-capture" || command == "compositor-capture" {
            guard args.count == 3 else { throw ProbeFailure("capture PID OUTPUT.png") }
            guard CGPreflightScreenCaptureAccess() else { throw ProbeFailure("Screen Recording permission is absent for this probe process") }
            let content = try await SCShareableContent.excludingDesktopWindows(true, onScreenWindowsOnly: true)
            guard let window = content.windows.first(where: { $0.owningApplication?.processID == pid && $0.windowLayer == 0 }) else {
                throw ProbeFailure("No visible browser window")
            }
            let configuration = SCStreamConfiguration()
            let filter: SCContentFilter
            var frame = window.frame
            if command == "display-capture" || command == "compositor-capture" {
                guard let display = content.displays.first(where: { $0.frame.intersects(window.frame) }) else {
                    throw ProbeFailure("No display contains the target window")
                }
                if command == "compositor-capture" {
                    app.activate(options: [])
                    try await Task.sleep(for: .milliseconds(300))
                    guard NSWorkspace.shared.frontmostApplication?.processIdentifier == pid else {
                        throw ProbeFailure("Research target is not frontmost; refusing compositor crop")
                    }
                    // Crop inside the opaque research window to exclude other apps and rounded corners.
                    frame = window.frame.insetBy(dx: 24, dy: 48)
                    filter = SCContentFilter(display: display, excludingWindows: [])
                } else {
                    filter = SCContentFilter(display: display, including: [window])
                }
                configuration.sourceRect = frame.offsetBy(dx: -display.frame.minX, dy: -display.frame.minY)
            } else {
                filter = SCContentFilter(desktopIndependentWindow: window)
            }
            configuration.width = Int(frame.width * 2)
            configuration.height = Int(frame.height * 2)
            configuration.showsCursor = false
            let image = try await SCScreenshotManager.captureImage(contentFilter: filter, configuration: configuration)
            if command == "compositor-capture", NSWorkspace.shared.frontmostApplication?.processIdentifier != pid {
                throw ProbeFailure("Research target lost foreground focus; discarding compositor crop")
            }
            let url = URL(fileURLWithPath: args[2])
            guard let destination = CGImageDestinationCreateWithURL(url as CFURL, UTType.png.identifier as CFString, 1, nil) else {
                throw ProbeFailure("Cannot create PNG output")
            }
            CGImageDestinationAddImage(destination, image, nil)
            guard CGImageDestinationFinalize(destination) else { throw ProbeFailure("Cannot write capture") }
            try emit(["status": "captured", "pid": pid, "windowID": window.windowID,
                      "frame": [frame.minX, frame.minY, frame.width, frame.height],
                      "pixels": [image.width, image.height], "path": url.path])
            return
        }
        throw ProbeFailure("Unknown command")
    }
}

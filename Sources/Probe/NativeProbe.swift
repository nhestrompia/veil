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

func savePNG(_ image: CGImage, path: String) throws {
    let url = URL(fileURLWithPath: path)
    guard let destination = CGImageDestinationCreateWithURL(url as CFURL, UTType.png.identifier as CFString, 1, nil) else {
        throw ProbeFailure("Cannot create PNG output")
    }
    CGImageDestinationAddImage(destination, image, nil)
    guard CGImageDestinationFinalize(destination) else { throw ProbeFailure("Cannot write capture") }
}

func frameOfWindow(_ window: [String: Any]) -> CGRect? {
    guard let bounds = window[kCGWindowBounds as String] as? [String: Any] else { return nil }
    return CGRect(dictionaryRepresentation: bounds as CFDictionary)
}

@MainActor
func verifyResearchBackdrop(pid: pid_t, targetID: CGWindowID, backdropID: CGWindowID, region: CGRect) throws {
    guard NSWorkspace.shared.frontmostApplication?.processIdentifier == pid else {
        throw ProbeFailure("Research target is not frontmost")
    }
    let windows = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] ?? []
    guard let targetIndex = windows.firstIndex(where: { ($0[kCGWindowNumber as String] as? UInt32) == targetID }),
          let backdropIndex = windows.firstIndex(where: { ($0[kCGWindowNumber as String] as? UInt32) == backdropID }),
          targetIndex < backdropIndex else { throw ProbeFailure("Research window ordering is invalid") }
    let target = windows[targetIndex], backdrop = windows[backdropIndex]
    guard (target[kCGWindowOwnerPID as String] as? Int32) == pid,
          (backdrop[kCGWindowOwnerPID as String] as? Int32) == pid,
          (target[kCGWindowAlpha as String] as? Double) == 1,
          (backdrop[kCGWindowAlpha as String] as? Double) == 1,
          let targetFrame = frameOfWindow(target), let backdropFrame = frameOfWindow(backdrop),
          targetFrame.contains(region), backdropFrame.contains(region),
          (backdrop[kCGWindowLayer as String] as? Int ?? 0) >= Int(CGWindowLevelForKey(.screenSaverWindow)) else {
        throw ProbeFailure("The opaque owned research backdrop does not cover the capture region")
    }
    for window in windows.prefix(backdropIndex) {
        if (window[kCGWindowOwnerPID as String] as? Int32) == pid { continue }
        if (window[kCGWindowLayer as String] as? Int) == Int(CGWindowLevelForKey(.cursorWindow)) { continue }
        if (window[kCGWindowAlpha as String] as? Double ?? 1) > 0, let frame = frameOfWindow(window), frame.intersects(region) {
            throw ProbeFailure("A non-research overlay intersects the capture region")
        }
    }
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
func requestedPostingTap() -> CGEventTapLocation {
    if CommandLine.arguments.contains("--session-tap") { return .cgSessionEventTap }
    if CommandLine.arguments.contains("--annotated-tap") { return .cgAnnotatedSessionEventTap }
    return .cghidEventTap
}

@MainActor
func post(_ event: CGEvent, pid: pid_t?, targetPID: pid_t) throws {
    if let pid {
        event.postToPid(pid)
    } else {
        if ![CGEventType.leftMouseUp, .rightMouseUp, .otherMouseUp, .keyUp, .flagsChanged].contains(event.type) {
            try DesktopInputSafety.observe().requireIsolatedMouse()
        }
        guard NSWorkspace.shared.frontmostApplication?.processIdentifier == targetPID else {
            throw ProbeFailure("Target lost foreground focus; refusing further global input")
        }
        event.post(tap: requestedPostingTap())
    }
}

@MainActor
func sendKey(_ code: CGKeyCode, flags: CGEventFlags = [], pid: pid_t? = nil, source: CGEventSource?, targetPID: pid_t) throws {
    var pressed = false
    defer {
        if pressed {
            let release = CGEvent(keyboardEventSource: source, virtualKey: code, keyDown: false)
            release?.flags = []
            if let pid { release?.postToPid(pid) } else { release?.post(tap: requestedPostingTap()) }
        }
    }
    for down in [true, false] {
        guard let event = CGEvent(keyboardEventSource: source, virtualKey: code, keyDown: down) else {
            throw ProbeFailure("Cannot construct keyboard event")
        }
        event.flags = down ? flags : []
        try post(event, pid: pid, targetPID: targetPID)
        pressed = down
        Thread.sleep(forTimeInterval: 0.03)
    }
}

@MainActor
func typeText(_ text: String, pid: pid_t? = nil, source: CGEventSource?, targetPID: pid_t) throws {
    for character in text.utf16 {
        var unit = character
        var pressed = false
        defer {
            if pressed {
                let release = CGEvent(keyboardEventSource: source, virtualKey: 0, keyDown: false)
                release?.flags = []
                if let pid { release?.postToPid(pid) } else { release?.post(tap: requestedPostingTap()) }
            }
        }
        for down in [true, false] {
            guard let event = CGEvent(keyboardEventSource: source, virtualKey: 0, keyDown: down) else {
                throw ProbeFailure("Cannot construct text event")
            }
            event.keyboardSetUnicodeString(stringLength: 1, unicodeString: &unit)
            event.flags = []
            try post(event, pid: pid, targetPID: targetPID)
            pressed = down
        }
        Thread.sleep(forTimeInterval: 0.04)
    }
}

@MainActor
func click(_ point: CGPoint, pid: pid_t? = nil, source: CGEventSource?, targetPID: pid_t,
           routedWindow: CGWindowID? = nil) throws {
    var pressed = false
    defer {
        if pressed {
            let location = CGEvent(source: nil)?.location ?? point
            let release = CGEvent(mouseEventSource: source, mouseType: .leftMouseUp,
                                  mouseCursorPosition: location, mouseButton: .left)
            release?.flags = []
            if let pid { release?.postToPid(pid) } else { release?.post(tap: requestedPostingTap()) }
        }
    }
    for type in [CGEventType.mouseMoved, .leftMouseDown, .leftMouseUp] {
        guard let event = CGEvent(mouseEventSource: source, mouseType: type, mouseCursorPosition: point, mouseButton: .left) else {
            throw ProbeFailure("Cannot construct mouse event")
        }
        if let routedWindow {
            event.setIntegerValueField(.mouseEventWindowUnderMousePointer, value: Int64(routedWindow))
            event.setIntegerValueField(.mouseEventWindowUnderMousePointerThatCanHandleThisEvent, value: Int64(routedWindow))
            if type != .mouseMoved {
                event.setIntegerValueField(.mouseEventClickState, value: 1)
                event.setIntegerValueField(.mouseEventNumber, value: 1)
            }
        }
        try post(event, pid: pid, targetPID: targetPID)
        if type == .leftMouseDown { pressed = true }
        if type == .leftMouseUp { pressed = false }
        Thread.sleep(forTimeInterval: 0.08)
    }
}

@main
enum NativeProbe {
    @MainActor static func main() async {
        if let index = CommandLine.arguments.firstIndex(of: "--out"), CommandLine.arguments.indices.contains(index + 1) {
            let path = URL(fileURLWithPath: CommandLine.arguments[index + 1]).appendingPathExtension("pid")
            do { try String(getpid()).write(to: path, atomically: true, encoding: .utf8) }
            catch { exit(2) }
        }
        _ = NSApplication.shared
        var arguments = Array(CommandLine.arguments.dropFirst())
        if let index = arguments.firstIndex(of: "--out"), arguments.indices.contains(index + 1) {
            arguments.removeSubrange(index...index + 1)
        }
        arguments.removeAll { $0 == "--session-tap" || $0 == "--annotated-tap" }
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
                      "postEvents": CGPreflightPostEventAccess(), "screenCapture": CGPreflightScreenCaptureAccess(),
                      "desktopInputSafety": DesktopInputSafety.observe().report])
            return
        }
        if command == "request-permissions" {
            let accessibility = AXIsProcessTrusted()
            let postEvents = CGRequestPostEventAccess()
            let screenCapture = CGRequestScreenCaptureAccess()
            try emit(["accessibility": accessibility, "postEvents": postEvents, "screenCapture": screenCapture])
            return
        }
        if ["bootstrap-input", "input", "hid-post-input", "research-drag"].contains(command) {
            try DesktopInputSafety.observe().requireIsolatedMouse()
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
        if command == "research-drag" {
            guard args.count == 5, let x = Double(args[3]), let y = Double(args[4]) else {
                throw ProbeFailure("research-drag TARGET_PID SOURCE_PID X Y")
            }
            try await dragResearchPayload(target: app, source: target(args[2]), point: CGPoint(x: x, y: y))
            return
        }
        if command == "compositor-capture" {
            throw ProbeFailure("Use isolated-compositor-capture with a verified research backdrop")
        }
        if command == "isolated-compositor-capture" || command == "isolated-stream-capture" {
            guard args.count == 5, app.bundleIdentifier == "research.agentfreebrowser.internalkeyboardcontrol",
                  let targetID = CGWindowID(args[2]), let backdropID = CGWindowID(args[3]), targetID != backdropID else {
                throw ProbeFailure("Use the internal diagnostic with two distinct owned window IDs")
            }
            guard CGPreflightScreenCaptureAccess() else { throw ProbeFailure("Screen Recording permission is absent for this probe process") }
            app.activate(options: [])
            try await Task.sleep(for: .milliseconds(300))
            let content = try await SCShareableContent.excludingDesktopWindows(true, onScreenWindowsOnly: true)
            guard let window = content.windows.first(where: { $0.windowID == targetID && $0.owningApplication?.processID == pid }),
                  content.windows.contains(where: { $0.windowID == backdropID && $0.owningApplication?.processID == pid }),
                  let display = content.displays.first(where: { $0.frame.contains(window.frame) }) else {
                throw ProbeFailure("The two research windows are not available on one display")
            }
            let region = window.frame.insetBy(dx: 24, dy: 48)
            try verifyResearchBackdrop(pid: pid, targetID: targetID, backdropID: backdropID, region: region)
            let configuration = SCStreamConfiguration()
            configuration.sourceRect = region.offsetBy(dx: -display.frame.minX, dy: -display.frame.minY)
            configuration.width = Int(region.width * 2)
            configuration.height = Int(region.height * 2)
            configuration.showsCursor = false
            let filter = SCContentFilter(display: display, excludingWindows: [])
            let image: CGImage
            if command == "isolated-stream-capture" {
                image = try await firstCompleteStreamFrame(filter: filter, configuration: configuration)
            } else {
                image = try await SCScreenshotManager.captureImage(contentFilter: filter, configuration: configuration)
            }
            try verifyResearchBackdrop(pid: pid, targetID: targetID, backdropID: backdropID, region: region)
            try savePNG(image, path: args[4])
            try emit(["status": "captured", "pid": pid, "targetWindowID": targetID, "backdropWindowID": backdropID,
                      "frame": [region.minX, region.minY, region.width, region.height], "path": args[4],
                      "backdropVerifiedBeforeAndAfter": true, "method": command,
                      "filter": "unfiltered display cropped inside owned research coverage"])
            return
        }
        if command == "ax-direct" {
            guard AXIsProcessTrusted() else { throw ProbeFailure("Accessibility permission is absent for this probe process") }
            app.activate(options: [])
            try await Task.sleep(for: .milliseconds(300))
            guard NSWorkspace.shared.frontmostApplication?.processIdentifier == pid else {
                throw ProbeFailure("Research target is not frontmost; refusing system-wide AX query")
            }
            let root = AXUIElementCreateApplication(pid)
            let system = AXUIElementCreateSystemWide()
            AXUIElementSetMessagingTimeout(root, 1)
            AXUIElementSetMessagingTimeout(system, 1)
            var roots: [AXUIElement] = [root]
            var queries: [[String: Any]] = []
            func appendOwned(_ value: CFTypeRef?, query: String, error: AXError) {
                var ownsElement = false
                if let value, CFGetTypeID(value) == AXUIElementGetTypeID() {
                    let element = value as! AXUIElement
                    var owner: pid_t = 0
                    if AXUIElementGetPid(element, &owner) == .success, owner == pid {
                        roots.append(element)
                        ownsElement = true
                    }
                }
                queries.append(["query": query, "error": error.rawValue, "ownedElement": ownsElement])
            }
            for (element, key) in [(root, kAXMainWindowAttribute), (root, kAXFocusedWindowAttribute),
                                   (root, kAXFocusedUIElementAttribute), (system, kAXFocusedUIElementAttribute)] {
                var value: CFTypeRef?
                let error = AXUIElementCopyAttributeValue(element, key as CFString, &value)
                appendOwned(value, query: (element == system ? "system:" : "application:") + key, error: error)
            }
            let windows = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] ?? []
            if let window = windows.first(where: { ($0[kCGWindowOwnerPID as String] as? Int32) == pid && ($0[kCGWindowLayer as String] as? Int) == 0 }),
               let bounds = window[kCGWindowBounds as String] as? [String: Any],
               let frame = CGRect(dictionaryRepresentation: bounds as CFDictionary) {
                for point in [CGPoint(x: frame.midX, y: frame.midY), CGPoint(x: frame.minX + 320, y: frame.minY + 360)] where frame.insetBy(dx: 24, dy: 24).contains(point) {
                    guard NSWorkspace.shared.frontmostApplication?.processIdentifier == pid else {
                        throw ProbeFailure("Target lost foreground focus; refusing further AX hit tests")
                    }
                    var value: AXUIElement?
                    let error = AXUIElementCopyElementAtPosition(system, Float(point.x), Float(point.y), &value)
                    appendOwned(value, query: "system:hit-test", error: error)
                }
            }
            var seen: Set<AXUIElement> = []
            let observed = roots.flatMap(elements).filter { element in
                var owner: pid_t = 0
                return AXUIElementGetPid(element, &owner) == .success && owner == pid && seen.insert(element).inserted
            }
            try emit(["status": "observed", "queries": queries, "elements": observed.map(description),
                      "scope": "Only exact target-PID elements; File/Edit use the separate menu adapter"])
            return
        }
        if command == "bootstrap-input" {
            guard args.count == 3, ["session", "hid", "private", "iohid-legacy", "iohid-reports"].contains(args[2]) else {
                throw ProbeFailure("bootstrap-input PID session|hid|private|iohid-legacy|iohid-reports")
            }
            guard CGPreflightPostEventAccess() else { throw ProbeFailure("Event-posting permission is absent for this probe process") }
            app.activate(options: [])
            try await Task.sleep(for: .milliseconds(300))
            var connection: UInt32 = 0
            var statuses: [Int32] = []
            let usesHIDPosting = args[2].hasPrefix("iohid-")
            if usesHIDPosting {
                let result = AFBOpenHIDPosting(&connection)
                guard result == 0 else {
                    try emit(["status": "inconclusive", "openResult": result])
                    return
                }
            }
            defer { if usesHIDPosting { AFBCloseHIDPosting(connection) } }
            let sourceID: CGEventSourceStateID = args[2] == "session" ? .combinedSessionState : args[2] == "private" ? .privateState : .hidSystemState
            let source = CGEventSource(stateID: sourceID)
            let codes: [UInt16] = [49, 36, 48, 45, 0, 17, 34, 9, 14, 27, 34, 45, 35, 32, 17, 36]
            let characters = Array(" \r\tnative-input\r".utf16)
            for (index, pair) in zip(codes, characters).enumerated() {
                guard NSWorkspace.shared.frontmostApplication?.processIdentifier == pid else {
                    throw ProbeFailure("Target lost foreground focus; refusing bootstrap input")
                }
                let (code, character) = pair
                if usesHIDPosting {
                    for down: Int32 in [1, 0] {
                        guard NSWorkspace.shared.frontmostApplication?.processIdentifier == pid else {
                            throw ProbeFailure("Target lost foreground focus; refusing HID bootstrap input")
                        }
                        statuses.append(AFBPostHIDKey(connection, code, character, down, args[2] == "iohid-reports" ? 1 : 0))
                        try await Task.sleep(for: .milliseconds(35))
                    }
                } else {
                    try sendKey(code, source: source, targetPID: pid)
                }
                if index == 1 { try await Task.sleep(for: .seconds(1)) }
            }
            try emit(["status": "attempted", "route": args[2], "postResults": statuses,
                      "sequence": "Space, Return, Tab, fixed fake token, Return", "keyPairs": codes.count])
            return
        }
        if command == "ax-menu" {
            guard args.count == 3, ["inspect", "open-location"].contains(args[2]) else {
                throw ProbeFailure("ax-menu PID inspect|open-location")
            }
            guard AXIsProcessTrusted() else { throw ProbeFailure("Accessibility permission is absent for this probe process") }
            app.activate(options: [])
            try await Task.sleep(for: .milliseconds(300))
            let root = AXUIElementCreateApplication(pid)
            AXUIElementSetMessagingTimeout(root, 1)
            var rawMenu: CFTypeRef?
            let menuError = AXUIElementCopyAttributeValue(root, kAXMenuBarAttribute as CFString, &rawMenu)
            guard let rawMenu, CFGetTypeID(rawMenu) == AXUIElementGetTypeID() else {
                try emit(["status": "observed", "menuFound": false, "menuError": menuError.rawValue])
                return
            }
            let menu = rawMenu as! AXUIElement
            // Read only the research app's File and Edit menus, never system or recent-document menus.
            let topItems = attribute(menu, kAXChildrenAttribute) as? [AXUIElement] ?? []
            let safeMenus = topItems.filter { ["File", "Edit"].contains(attribute($0, kAXTitleAttribute) as? String ?? "") }
            var items: [AXUIElement] = []
            for top in safeMenus {
                let children = attribute(top, kAXChildrenAttribute) as? [AXUIElement] ?? []
                for child in children where attribute(child, kAXRoleAttribute) as? String == kAXMenuRole {
                    items += attribute(child, kAXChildrenAttribute) as? [AXUIElement] ?? []
                }
            }
            var result: [String: Any] = ["status": "observed", "menuFound": true, "menuError": menuError.rawValue,
                "items": items.map { ["title": attribute($0, kAXTitleAttribute) as? String ?? "",
                                      "enabled": attribute($0, kAXEnabledAttribute) as? Bool ?? false] }]
            if args[2] == "open-location" {
                guard let item = items.first(where: { attribute($0, kAXTitleAttribute) as? String == "Open Location..." }) else {
                    result["reason"] = "The research navigation action is absent"
                    try emit(result)
                    return
                }
                guard NSWorkspace.shared.frontmostApplication?.processIdentifier == pid else {
                    throw ProbeFailure("Target lost foreground focus; refusing menu action")
                }
                result["status"] = "attempted"
                result["actionError"] = AXUIElementPerformAction(item, kAXPressAction as CFString).rawValue
            }
            try emit(result)
            return
        }
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
            let directed = args.contains("pid") || args.contains("pid-window") ? pid : nil
            let keyDirected = args.contains("pid-keys") ? pid : directed
            var routedWindow: CGWindowID?
            if args.contains("pid-window") {
                let windows = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] ?? []
                guard let window = windows.first(where: { ($0[kCGWindowOwnerPID as String] as? Int32) == pid &&
                    ($0[kCGWindowLayer as String] as? Int) == 0 }), let id = window[kCGWindowNumber as String] as? UInt32 else {
                    throw ProbeFailure("No verified research window for directed mouse routing")
                }
                routedWindow = id
            }
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
            try click(CGPoint(x: x, y: y), pid: directed, source: source, targetPID: pid, routedWindow: routedWindow)
            if args.contains("keycodes") {
                for code: CGKeyCode in [45, 0, 17, 34, 9, 14, 27, 34, 45, 35, 32, 17] {
                    try sendKey(code, pid: keyDirected, source: source, targetPID: pid)
                }
            } else {
                try typeText("native-input", pid: keyDirected, source: source, targetPID: pid)
            }
            try sendKey(36, pid: keyDirected, source: source, targetPID: pid)
            try emit(["status": "attempted", "pid": pid, "source": args[4],
                      "postTap": requestedPostingTap().rawValue,
                      "directToPID": directed != nil, "keyboardDirectToPID": keyDirected != nil,
                      "explicitWindowRouting": routedWindow != nil,
                      "curvedTrajectory": args.contains("curve")])
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
        if command == "capture" || command == "display-capture" {
            guard args.count == 3 else { throw ProbeFailure("capture PID OUTPUT.png") }
            guard CGPreflightScreenCaptureAccess() else { throw ProbeFailure("Screen Recording permission is absent for this probe process") }
            let content = try await SCShareableContent.excludingDesktopWindows(true, onScreenWindowsOnly: true)
            guard let window = content.windows.first(where: { $0.owningApplication?.processID == pid && $0.windowLayer == 0 }) else {
                throw ProbeFailure("No visible browser window")
            }
            let configuration = SCStreamConfiguration()
            let filter: SCContentFilter
            let frame = window.frame
            if command == "display-capture" {
                guard let display = content.displays.first(where: { $0.frame.intersects(window.frame) }) else {
                    throw ProbeFailure("No display contains the target window")
                }
                filter = SCContentFilter(display: display, including: [window])
                configuration.sourceRect = frame.offsetBy(dx: -display.frame.minX, dy: -display.frame.minY)
            } else {
                filter = SCContentFilter(desktopIndependentWindow: window)
            }
            configuration.width = Int(frame.width * 2)
            configuration.height = Int(frame.height * 2)
            configuration.showsCursor = false
            let image = try await SCScreenshotManager.captureImage(contentFilter: filter, configuration: configuration)
            try savePNG(image, path: args[2])
            try emit(["status": "captured", "pid": pid, "windowID": window.windowID,
                      "frame": [frame.minX, frame.minY, frame.width, frame.height],
                      "pixels": [image.width, image.height], "path": URL(fileURLWithPath: args[2]).path])
            return
        }
        throw ProbeFailure("Unknown command")
    }
}

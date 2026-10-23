import AppKit
import WebKit

@main
enum InspectorLaunchControl {
    @MainActor static func main() throws {
        let arguments = CommandLine.arguments
        guard let index = arguments.firstIndex(of: "--out"), arguments.indices.contains(index + 1) else {
            throw CocoaError(.fileWriteInvalidFileName)
        }
        let requestedDefault = UserDefaults.standard.bool(forKey: "WebKitDebugDeveloperExtrasEnabled")
        let applyPolicy = arguments.contains("--apply-policy")
        let policyAccepted = applyPolicy ? BrowserRuntimePolicy.disableDeveloperExtras() : false
        _ = NSApplication.shared
        let configuration = WKWebViewConfiguration()
        configuration.websiteDataStore = .nonPersistent()
        let preferences = configuration.preferences
        let selector = NSSelectorFromString("_developerExtrasEnabled")
        let supported = preferences.responds(to: selector)
        let extras = supported ? preferences.value(forKey: "_developerExtrasEnabled") as? Bool : nil
        let view = WKWebView(frame: .zero, configuration: configuration)
        view.isInspectable = false
        let result: [String: Any] = [
            "pid": ProcessInfo.processInfo.processIdentifier,
            "macOS": ProcessInfo.processInfo.operatingSystemVersionString,
            "getterSupported": supported,
            "requestedLaunchDefault": requestedDefault,
            "policyApplied": applyPolicy,
            "policyAccepted": policyAccepted,
            "unrelatedArgumentPreserved": UserDefaults.standard.string(forKey: "ResearchSentinel") == "preserve-me",
            "developerExtrasEnabled": extras as Any? ?? NSNull(),
            "effectiveLaunchDefault": UserDefaults.standard.bool(forKey: "WebKitDebugDeveloperExtrasEnabled"),
            "isInspectable": view.isInspectable,
            "scope": "Diagnostic property read only. No inspector attachment, page, or external browser action."
        ]
        let data = try JSONSerialization.data(withJSONObject: result, options: [.prettyPrinted, .sortedKeys])
        try data.write(to: URL(fileURLWithPath: arguments[index + 1]), options: .atomic)
    }
}

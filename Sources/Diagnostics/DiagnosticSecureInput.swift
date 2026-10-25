import AppKit
import WebKit
import ObjectiveC.runtime

// Read only this process's view bookkeeping. This does not prove OS protection.
@MainActor
enum DiagnosticSecureInput {
    static func owner(in view: NSView?) -> String {
        guard let view else { return "no-view" }
        if let webView = view as? WKWebView {
            let selector = NSSelectorFromString("_secureEventInputEnabledForTesting")
            guard let method = class_getInstanceMethod(type(of: webView), selector),
                  method_getNumberOfArguments(method) == 2 else { return "unavailable" }
            let returnType = method_copyReturnType(method)
            defer { free(returnType) }
            guard String(cString: returnType) == "B" else { return "wrong-signature" }
            typealias Getter = @convention(c) (AnyObject, Selector) -> Bool
            let getter = unsafeBitCast(method_getImplementation(method), to: Getter.self)
            return getter(webView, selector) ? "true" : "false"
        }
        for child in view.subviews {
            let result = owner(in: child)
            if result != "no-view" { return result }
        }
        return "no-view"
    }
}

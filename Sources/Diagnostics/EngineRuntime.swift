import AppKit
import WebKit
import ObjectiveC.runtime
import MachO
import Darwin

@MainActor
enum EngineRuntime {
    static func stablePolicy(in configuration: WKWebViewConfiguration) -> Bool? {
        let selector = NSSelectorFromString("_usesStablePageActivityForResearch")
        guard let method = class_getInstanceMethod(WKWebViewConfiguration.self, selector),
              method_getNumberOfArguments(method) == 2 else { return nil }
        let returnType = method_copyReturnType(method)
        defer { free(returnType) }
        guard String(cString: returnType) == "B" else { return nil }
        typealias Getter = @convention(c) (AnyObject, Selector) -> Bool
        return unsafeBitCast(method_getImplementation(method), to: Getter.self)(configuration, selector)
    }

    static func configure(_ configuration: WKWebViewConfiguration, stable: Bool) -> Bool {
        guard let root = frameworkRoot,
              let image = class_getImageName(WKWebView.self),
              URL(fileURLWithPath: String(cString: image)).resolvingSymlinksInPath().path.hasPrefix(root + "/") else {
            print("ENGINE_DIAGNOSTIC refused=unexpected-ui-framework")
            return false
        }
        let requiredImages: Set<String> = ["WebKit", "WebCore", "JavaScriptCore"]
        var observedImages: Set<String> = []
        for index in 0..<_dyld_image_count() {
            guard let imageName = _dyld_get_image_name(index) else { continue }
            let url = URL(fileURLWithPath: String(cString: imageName)).resolvingSymlinksInPath()
            guard requiredImages.contains(url.lastPathComponent) else { continue }
            guard url.path.hasPrefix(root + "/") else { return false }
            observedImages.insert(url.lastPathComponent)
            print("ENGINE_DIAGNOSTIC uiLoadedImage=\(url.path)")
        }
        guard observedImages == requiredImages else { return false }
        let setter = NSSelectorFromString("_setUsesStablePageActivityForResearch:")
        let getter = NSSelectorFromString("_usesStablePageActivityForResearch")
        guard let setMethod = class_getInstanceMethod(WKWebViewConfiguration.self, setter),
              let getMethod = class_getInstanceMethod(WKWebViewConfiguration.self, getter),
              method_getNumberOfArguments(setMethod) == 3,
              method_getNumberOfArguments(getMethod) == 2,
              let setterArgument = method_copyArgumentType(setMethod, 2) else { return false }
        let setterReturn = method_copyReturnType(setMethod)
        let getterReturn = method_copyReturnType(getMethod)
        defer { free(setterReturn); free(setterArgument); free(getterReturn) }
        guard String(cString: setterReturn) == "v", String(cString: setterArgument) == "B",
              String(cString: getterReturn) == "B" else { return false }
        typealias Setter = @convention(c) (AnyObject, Selector, Bool) -> Void
        typealias Getter = @convention(c) (AnyObject, Selector) -> Bool
        let set = unsafeBitCast(method_getImplementation(setMethod), to: Setter.self)
        let get = unsafeBitCast(method_getImplementation(getMethod), to: Getter.self)
        set(configuration, setter, stable)
        guard get(configuration, getter) == stable else { return false }
        print("ENGINE_DIAGNOSTIC uiFramework=\(String(cString: image)) stable=\(stable)")
        return true
    }

    struct ContentIdentity {
        let pid: Int32
        let executable: URL
    }

    static func contentIdentity(_ webView: WKWebView) -> ContentIdentity? {
        let selector = NSSelectorFromString("_webProcessIdentifier")
        guard let root = frameworkRoot,
              let method = class_getInstanceMethod(WKWebView.self, selector),
              method_getNumberOfArguments(method) == 2 else { return nil }
        let returnType = method_copyReturnType(method)
        defer { free(returnType) }
        guard String(cString: returnType) == "i" else { return nil }
        typealias Getter = @convention(c) (AnyObject, Selector) -> Int32
        let getter = unsafeBitCast(method_getImplementation(method), to: Getter.self)
        let pid = getter(webView, selector)
        var pathBytes = [CChar](repeating: 0, count: 4 * Int(MAXPATHLEN))
        guard pid > 0, proc_pidpath(pid, &pathBytes, UInt32(pathBytes.count)) > 0 else { return nil }
        let path = String(decoding: pathBytes.prefix(while: { $0 != 0 }).map { UInt8(bitPattern: $0) }, as: UTF8.self)
        let executable = URL(fileURLWithPath: path).resolvingSymlinksInPath()
        guard executable.path.hasPrefix(root + "/") else {
            print("ENGINE_DIAGNOSTIC refused=unexpected-content-executable")
            return nil
        }
        return ContentIdentity(pid: pid, executable: executable)
    }

    static func reportContent(_ webView: WKWebView) -> Bool {
        guard let identity = contentIdentity(webView) else { return false }
        print("ENGINE_DIAGNOSTIC contentPID=\(identity.pid) contentExecutable=\(identity.executable.path)")
        fflush(stdout)
        return true
    }

    private static var frameworkRoot: String? {
        guard let path = ProcessInfo.processInfo.environment["AFB_RESEARCH_FRAMEWORK_ROOT"] else { return nil }
        return URL(fileURLWithPath: path).resolvingSymlinksInPath().path
    }
}

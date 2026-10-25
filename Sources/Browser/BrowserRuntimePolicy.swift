import Foundation
import AppKit
import WebKit
import ObjectiveC

@MainActor
enum BrowserRuntimePolicy {
    static let deniedFeatures = ["WebShareEnabled", "AsyncClipboardAPIEnabled", "WebAuthenticationEnabled", "ApplePayEnabled"]

    static func featureState(in preferences: WKPreferences, disable: Bool,
                             requiredFeatures: [String] = deniedFeatures) -> [String: Bool]? {
        let listSelector = NSSelectorFromString("_features")
        let setSelector = NSSelectorFromString("_setEnabled:forFeature:")
        let getSelector = NSSelectorFromString("_isEnabledForFeature:")
        guard let listMethod = class_getClassMethod(WKPreferences.self, listSelector),
              preferences.responds(to: setSelector), preferences.responds(to: getSelector),
              let setter = preferences.method(for: setSelector), let getter = preferences.method(for: getSelector) else { return nil }
        typealias List = @convention(c) (AnyClass, Selector) -> Unmanaged<NSArray>
        typealias SetFeature = @convention(c) (AnyObject, Selector, Bool, AnyObject) -> Void
        typealias GetFeature = @convention(c) (AnyObject, Selector, AnyObject) -> Bool
        // These SPI signatures match WKPreferencesPrivate.h. Unknown keys must fail closed.
        let list = unsafeBitCast(method_getImplementation(listMethod), to: List.self)
        let set = unsafeBitCast(setter, to: SetFeature.self)
        let get = unsafeBitCast(getter, to: GetFeature.self)
        var features: [String: NSObject] = [:]
        let keySelector = NSSelectorFromString("key")
        for case let feature as NSObject in list(WKPreferences.self, listSelector).takeUnretainedValue() {
            guard feature.responds(to: keySelector),
                  let key = feature.perform(keySelector)?.takeUnretainedValue() as? String,
                  requiredFeatures.contains(key) else { continue }
            features[key] = feature
        }
        var result: [String: Bool] = [:]
        for key in requiredFeatures {
            guard let feature = features[key] else { continue }
            if disable { set(preferences, setSelector, false, feature) }
            result[key] = get(preferences, getSelector, feature)
        }
        return result
    }

    static func configureContent(_ configuration: WKWebViewConfiguration,
                                 requiredFeatures: [String] = deniedFeatures) -> Bool {
        configuration.preferences.isElementFullscreenEnabled = false
        if #available(macOS 15.0, *) {
            // The SDK hides this public property at a macOS 14 deployment target.
            guard configuration.responds(to: NSSelectorFromString("setWritingToolsBehavior:")),
                  configuration.responds(to: NSSelectorFromString("writingToolsBehavior")) else { return false }
            configuration.setValue(NSWritingToolsBehavior.none.rawValue, forKey: "writingToolsBehavior")
            guard configuration.value(forKey: "writingToolsBehavior") as? Int == NSWritingToolsBehavior.none.rawValue else { return false }
        }
        guard let features = featureState(in: configuration.preferences, disable: true, requiredFeatures: requiredFeatures) else { return false }
        return Set(features.keys) == Set(requiredFeatures) && features.values.allSatisfy { !$0 }
    }

    static func contentIsRestricted(_ configuration: WKWebViewConfiguration) -> Bool {
        guard !configuration.websiteDataStore.isPersistent, !configuration.preferences.isElementFullscreenEnabled,
              let features = featureState(in: configuration.preferences, disable: false),
              Set(features.keys) == Set(deniedFeatures), features.values.allSatisfy({ !$0 }) else { return false }
        if #available(macOS 15.0, *) {
            guard configuration.responds(to: NSSelectorFromString("writingToolsBehavior")),
                  configuration.value(forKey: "writingToolsBehavior") as? Int == NSWritingToolsBehavior.none.rawValue else { return false }
        }
        return true
    }

    static func disableDeveloperExtras(in defaults: UserDefaults = .standard) -> Bool {
        let key = "WebKitDebugDeveloperExtrasEnabled"
        var arguments = defaults.volatileDomain(forName: UserDefaults.argumentDomain)
        arguments[key] = false
        defaults.setVolatileDomain(arguments, forName: UserDefaults.argumentDomain)
        return !defaults.bool(forKey: key)
    }
}

import Foundation

enum BrowserRuntimePolicy {
    static func disableDeveloperExtras(in defaults: UserDefaults = .standard) -> Bool {
        let key = "WebKitDebugDeveloperExtrasEnabled"
        var arguments = defaults.volatileDomain(forName: UserDefaults.argumentDomain)
        arguments[key] = false
        defaults.setVolatileDomain(arguments, forName: UserDefaults.argumentDomain)
        return !defaults.bool(forKey: key)
    }
}

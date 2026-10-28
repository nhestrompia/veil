import AppKit
import CryptoKit
import WebKit
import Darwin

@MainActor
enum FocusEngineRuntime {
    #if FOCUS_ENGINE_NATIVE_CONTROL
    static let stable = false
    #else
    static let stable = true
    #endif

    static func bootstrap() -> Bool {
        let environment = ProcessInfo.processInfo.environment
        let keys = ["AFB_RESEARCH_FRAMEWORK_ROOT", "DYLD_FRAMEWORK_PATH", "DYLD_LIBRARY_PATH",
                    "__XPC_DYLD_FRAMEWORK_PATH", "__XPC_DYLD_LIBRARY_PATH"]
        if keys.allSatisfy({ environment[$0] == FocusEnginePins.root }) { return preflight() }
        guard environment["AFB_FOCUS_ENGINE_BOOTSTRAPPED"] == nil,
              keys.allSatisfy({ environment[$0] == nil }), let executable = Bundle.main.executableURL else {
            print("FOCUS_ENGINE refused=unexpected-bootstrap-environment")
            return false
        }
        for key in environment.keys where key.hasPrefix("DYLD_") || key.hasPrefix("__XPC_DYLD_") {
            unsetenv(key)
        }
        for key in keys { setenv(key, FocusEnginePins.root, 1) }
        setenv("WEBKIT_UNSET_DYLD_FRAMEWORK_PATH", "YES", 1)
        setenv("AFB_FOCUS_ENGINE_BOOTSTRAPPED", "1", 1)
        execv(executable.path, CommandLine.unsafeArgv)
        print("FOCUS_ENGINE refused=bootstrap-exec")
        return false
    }

    static func preflight() -> Bool {
        let environment = ProcessInfo.processInfo.environment
        let expected = URL(fileURLWithPath: FocusEnginePins.root).resolvingSymlinksInPath().path
        let keys = ["AFB_RESEARCH_FRAMEWORK_ROOT", "DYLD_FRAMEWORK_PATH", "DYLD_LIBRARY_PATH",
                    "__XPC_DYLD_FRAMEWORK_PATH", "__XPC_DYLD_LIBRARY_PATH"]
        guard keys.allSatisfy({ environment[$0] == expected }) else {
            print("FOCUS_ENGINE refused=launch-environment use=tools/launch_focus_browser.py")
            return false
        }
        for (relative, digest) in FocusEnginePins.hashes {
            let path = URL(fileURLWithPath: expected).appendingPathComponent(relative).resolvingSymlinksInPath()
            guard path.path.hasPrefix(expected + "/"), hash(path) == digest else {
                print("FOCUS_ENGINE refused=engine-image")
                return false
            }
        }
        return true
    }

    static func configure(_ configuration: WKWebViewConfiguration) -> Bool {
        guard preflight(), EngineRuntime.configure(configuration, stable: stable),
              configurationMatches(configuration) else { return false }
        print("FOCUS_ENGINE configured=true stable=\(stable) nativeWindowState=true")
        return true
    }

    static func configurationMatches(_ configuration: WKWebViewConfiguration) -> Bool {
        EngineRuntime.stablePolicy(in: configuration) == stable
    }

    #if !BROWSER_NAVIGATION_CONTROL
    static func inputRequestApproved() -> Bool {
        let project = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
            .deletingLastPathComponent().deletingLastPathComponent()
        let manifest = project.appendingPathComponent("docs/evidence/focus-engine-browser-manifest.json")
        guard let data = try? Data(contentsOf: manifest),
              let record = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              record["permissionApproved"] as? Bool == true,
              let targets = record["targets"] as? [String: [String: Any]],
              let target = targets["AgentFreeBrowserEngine"],
              let executable = Bundle.main.executableURL?.resolvingSymlinksInPath(),
              let expected = target["binarySHA256"] as? String, let actual = hash(executable),
              target["path"] as? String == Bundle.main.bundleURL.resolvingSymlinksInPath().path,
              expected == actual else { return false }
        return true
    }
    #endif

    static func reportContent(_ view: WKWebView) -> Bool {
        guard configurationMatches(view.configuration), let identity = EngineRuntime.contentIdentity(view) else {
            print("FOCUS_ENGINE refused=content-identity")
            return false
        }
        let root = URL(fileURLWithPath: FocusEnginePins.root).resolvingSymlinksInPath().path + "/"
        let path = identity.executable.path
        guard path.hasPrefix(root),
              let digest = FocusEnginePins.hashes[String(path.dropFirst(root.count))],
              hash(identity.executable) == digest else {
            print("FOCUS_ENGINE refused=content-image")
            return false
        }
        print("ENGINE_DIAGNOSTIC contentPID=\(identity.pid) contentExecutable=\(path)")
        print("FOCUS_ENGINE contentVerified=true pid=\(identity.pid) stable=\(stable)")
        fflush(stdout)
        return true
    }

    private static func hash(_ path: URL) -> String? {
        guard let data = try? Data(contentsOf: path, options: .mappedIfSafe) else { return nil }
        return SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
    }
}

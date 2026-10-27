import AppKit
import WebKit
import ObjectiveC.runtime

@MainActor
enum ChannelProbeSupport {
    static func log(_ prefix: String, _ record: [String: Any]) {
        guard let data = try? JSONSerialization.data(withJSONObject: record, options: [.sortedKeys]) else { return }
        print(prefix + " " + String(decoding: data, as: UTF8.self))
        fflush(stdout)
    }

    static func arguments() -> (Int32, URL)? {
        let args = CommandLine.arguments
        guard getuid() >= 500, geteuid() == getuid(), args.count == 5,
              args[1] == "--channel", let fd = Int32(args[2]), args[3] == "--fixture",
              let url = URL(string: args[4]), url.scheme == "http", url.host == "127.0.0.1",
              let port = url.port, (1024...65535).contains(port), url.query == nil, url.fragment == nil,
              url.user == nil, url.password == nil,
              url.path.range(of: "\\A/channel/[0-9a-f]{16}\\z", options: .regularExpression) != nil else { return nil }
        return (fd, url)
    }

    static func identity() -> [String: Any] {
        var info = proc_bsdinfo()
        guard proc_pidinfo(getpid(), PROC_PIDTBSDINFO, 0, &info, Int32(MemoryLayout<proc_bsdinfo>.size)) == MemoryLayout<proc_bsdinfo>.size else { return [:] }
        return ["pid": getpid(), "startedSeconds": info.pbi_start_tvsec, "startedMicroseconds": info.pbi_start_tvusec]
    }

    static func roles(_ view: WKWebView) -> [String: Int32] {
        var result: [String: Int32] = [:]
        for (role, receiver, name): (String, NSObject, String) in [
            ("content", view, "_webProcessIdentifier"), ("gpu", view, "_gpuProcessIdentifier"),
            ("network", view.configuration.websiteDataStore, "_networkProcessIdentifier")] {
            let selector = NSSelectorFromString(name)
            guard let method = class_getInstanceMethod(type(of: receiver), selector), method_getNumberOfArguments(method) == 2 else { continue }
            let kind = method_copyReturnType(method)
            defer { free(kind) }
            guard String(cString: kind) == "i" else { continue }
            typealias Getter = @convention(c) (AnyObject, Selector) -> Int32
            result[role] = unsafeBitCast(method_getImplementation(method), to: Getter.self)(receiver, selector)
        }
        return result
    }
}

import AppKit
import Darwin

struct ResearchProcessIdentity: Equatable {
    let pid: pid_t
    let path: String
    let startedSeconds: UInt64
    let startedMicroseconds: UInt64

    init(pid: pid_t) throws {
        var info = proc_bsdinfo()
        let size = Int32(MemoryLayout<proc_bsdinfo>.size)
        guard proc_pidinfo(pid, PROC_PIDTBSDINFO, 0, &info, size) == size else {
            throw RendererScopeError.unavailableProcess
        }
        var bytes = [CChar](repeating: 0, count: 4 * Int(MAXPATHLEN))
        guard proc_pidpath(pid, &bytes, UInt32(bytes.count)) > 0 else {
            throw RendererScopeError.unavailableProcess
        }
        self.pid = pid
        path = String(decoding: bytes.prefix(while: { $0 != 0 }).map { UInt8(bitPattern: $0) }, as: UTF8.self)
        startedSeconds = info.pbi_start_tvsec
        startedMicroseconds = info.pbi_start_tvusec
    }
}

enum RendererScopeError: Error {
    case unavailableProcess
    case unavailableResponsibility
    case unrelatedHost
    case unrelatedRenderer
    case changedIdentity
}

enum RendererFixtureURL {
    static func parse(_ value: String) -> URL? {
        guard let url = URL(string: value), url.scheme == "http", url.host == "127.0.0.1",
              url.port == 8765, url.path.range(of: "\\A/trial/[0-9a-f]{16}\\z", options: .regularExpression) != nil,
              url.query == nil, url.fragment == nil, url.user == nil, url.password == nil else { return nil }
        return url
    }
}

enum RendererRemoteToken {
    static func data(pid: pid_t, elementID: UInt64) -> Data? {
        guard pid > 1 else { return nil }
        var result = Data()
        for var value in [UInt32(bitPattern: pid).littleEndian, UInt32(0), UInt32(0x636f636f).littleEndian] {
            withUnsafeBytes(of: &value) { result.append(contentsOf: $0) }
        }
        var identifier = elementID.littleEndian
        withUnsafeBytes(of: &identifier) { result.append(contentsOf: $0) }
        return result
    }
}

struct RendererOwnership {
    static let executable = "/System/Library/Frameworks/WebKit.framework/Versions/A/XPCServices/com.apple.WebKit.WebContent.xpc/Contents/MacOS/com.apple.WebKit.WebContent"
    static let cryptexExecutable = "/System/Volumes/Preboot/Cryptexes/OS" + executable

    static func permits(hostPID: pid_t, rendererPID: pid_t, rendererPath: String, responsiblePID: pid_t) -> Bool {
        hostPID > 1 && rendererPID > 1 && rendererPID != hostPID
            && [executable, cryptexExecutable].contains(rendererPath) && responsiblePID == hostPID
    }
}

@MainActor
final class RendererProcessScope {
    let host: ResearchProcessIdentity
    private let responsible: @convention(c) (pid_t) -> pid_t
    private let library: UnsafeMutableRawPointer

    init(hostPID: pid_t) throws {
        let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
        let names = ["research.agentfreebrowser.control": "InspectableControl",
                     "research.agentfreebrowser.devicekeyboard": "DeviceKeyboardExperiment"]
        guard let app = NSRunningApplication(processIdentifier: hostPID),
              let bundle = app.bundleIdentifier, let name = names[bundle] else {
            throw RendererScopeError.unrelatedHost
        }
        host = try ResearchProcessIdentity(pid: hostPID)
        let expected = root.appendingPathComponent("dist/\(name).app/Contents/MacOS/\(name)").path
        guard host.path == expected else { throw RendererScopeError.unrelatedHost }
        guard let handle = dlopen("/usr/lib/libproc.dylib", RTLD_LAZY | RTLD_LOCAL) else {
            throw RendererScopeError.unavailableResponsibility
        }
        guard let symbol = dlsym(handle, "responsibility_get_pid_responsible_for_pid") else {
            dlclose(handle)
            throw RendererScopeError.unavailableResponsibility
        }
        library = handle
        responsible = unsafeBitCast(symbol, to: (@convention(c) (pid_t) -> pid_t).self)
    }

    isolated deinit { dlclose(library) }

    func validateHost() throws {
        guard try ResearchProcessIdentity(pid: host.pid) == host else { throw RendererScopeError.changedIdentity }
    }

    func validate(_ renderer: ResearchProcessIdentity) throws {
        try validateHost()
        guard try ResearchProcessIdentity(pid: renderer.pid) == renderer else { throw RendererScopeError.changedIdentity }
        guard RendererOwnership.permits(hostPID: host.pid, rendererPID: renderer.pid,
                                       rendererPath: renderer.path, responsiblePID: responsible(renderer.pid)) else {
            throw RendererScopeError.unrelatedRenderer
        }
    }

    func renderers() throws -> [ResearchProcessIdentity] {
        try validateHost()
        let capacity = max(128, Int(proc_listallpids(nil, 0)) + 128)
        var pids = [pid_t](repeating: 0, count: capacity)
        let count = proc_listallpids(&pids, Int32(pids.count * MemoryLayout<pid_t>.size))
        guard count > 0, count <= capacity else { throw RendererScopeError.unavailableProcess }
        var result: [ResearchProcessIdentity] = []
        for pid in pids.prefix(Int(count)) where pid > 1 && pid != host.pid {
            guard responsible(pid) == host.pid, let identity = try? ResearchProcessIdentity(pid: pid),
                  RendererOwnership.permits(hostPID: host.pid, rendererPID: pid,
                                            rendererPath: identity.path, responsiblePID: responsible(pid)) else { continue }
            try validate(identity)
            result.append(identity)
        }
        return result.sorted { $0.pid < $1.pid }
    }
}

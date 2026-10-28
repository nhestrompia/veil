import AppKit
import CryptoKit
import Darwin

struct PreviewAXHostPolicy {
    let name: String
    let bundle: String
    let digest: String

    static let hosts = [
        PreviewAXHostPolicy(name: "AgentFreeBrowserPreview", bundle: "research.agentfreebrowser.preview",
                            digest: "dc3ca62c174d635b9994d9bae27ff6d4dc4a7983bc36d332f720fbbfaf24df70"),
        PreviewAXHostPolicy(name: "InspectableControl", bundle: "research.agentfreebrowser.control",
                            digest: "ac6b5b199ebfeafbeb53b85ad759c966bbd4f9b852cfc39ecd89af6b725bab36")
    ]

    func permits(bundle: String, path: String, digest: String, root: URL) -> Bool {
        bundle == self.bundle && digest == self.digest
            && path == root.appendingPathComponent("dist/\(name).app/Contents/MacOS/\(name)").path
    }

    static func markers(in text: String) -> [String] {
        let expression = try! NSRegularExpression(pattern: "AFB-[0-9A-F]{8}(?![0-9A-F])")
        return expression.matches(in: text, range: NSRange(text.startIndex..., in: text)).compactMap {
            Range($0.range, in: text).map { String(text[$0]) }
        }
    }
}

@MainActor
final class PreviewAXScope {
    let host: ResearchProcessIdentity
    let policy: PreviewAXHostPolicy
    private let responsible: @convention(c) (pid_t) -> pid_t
    private let library: UnsafeMutableRawPointer
    private let root: URL

    init(pid: pid_t, root: URL) throws {
        guard getuid() != 0, pid > 1, let app = NSRunningApplication(processIdentifier: pid),
              let bundle = app.bundleIdentifier,
              let policy = PreviewAXHostPolicy.hosts.first(where: { $0.bundle == bundle }) else {
            throw RendererScopeError.unrelatedHost
        }
        let identity = try ResearchProcessIdentity(pid: pid)
        let expected = root.appendingPathComponent("dist/\(policy.name).app/Contents/MacOS/\(policy.name)")
        guard policy.permits(bundle: bundle, path: identity.path, digest: try Self.hash(expected), root: root) else {
            throw RendererScopeError.unrelatedHost
        }
        guard let handle = dlopen("/usr/lib/libproc.dylib", RTLD_LAZY | RTLD_LOCAL) else {
            throw RendererScopeError.unavailableResponsibility
        }
        guard let symbol = dlsym(handle, "responsibility_get_pid_responsible_for_pid") else {
            dlclose(handle)
            throw RendererScopeError.unavailableResponsibility
        }
        library = handle
        responsible = unsafeBitCast(symbol, to: (@convention(c) (pid_t) -> pid_t).self)
        host = identity
        self.policy = policy
        self.root = root
        try validate(host)
    }

    isolated deinit { dlclose(library) }

    private static func hash(_ url: URL) throws -> String {
        SHA256.hash(data: try Data(contentsOf: url)).map { String(format: "%02x", $0) }.joined()
    }

    func validate(_ identity: ResearchProcessIdentity) throws {
        guard try ResearchProcessIdentity(pid: host.pid) == host,
              try ResearchProcessIdentity(pid: identity.pid) == identity else {
            throw RendererScopeError.changedIdentity
        }
        var info = proc_bsdinfo()
        let size = Int32(MemoryLayout<proc_bsdinfo>.size)
        guard proc_pidinfo(identity.pid, PROC_PIDTBSDINFO, 0, &info, size) == size,
              info.pbi_uid == getuid(), info.pbi_ruid == getuid() else { throw RendererScopeError.unrelatedRenderer }
        if identity == host { return }
        guard RendererOwnership.permits(hostPID: host.pid, rendererPID: identity.pid,
                                       rendererPath: identity.path, responsiblePID: responsible(identity.pid)) else {
            throw RendererScopeError.unrelatedRenderer
        }
    }

    func verifyImage() throws {
        try validate(host)
        guard try Self.hash(URL(fileURLWithPath: host.path)) == policy.digest else {
            throw RendererScopeError.changedIdentity
        }
    }

    func renderers() throws -> [ResearchProcessIdentity] {
        try verifyImage()
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
        guard result.count <= 4 else { throw RendererScopeError.unavailableProcess }
        return result.sorted { $0.pid < $1.pid }
    }
}

import Foundation

@main
enum PreviewAXScopeTests {
    static func main() {
        let root = URL(fileURLWithPath: "/test/project")
        for policy in PreviewAXHostPolicy.hosts {
            let path = root.appendingPathComponent("dist/\(policy.name).app/Contents/MacOS/\(policy.name)").path
            precondition(policy.permits(bundle: policy.bundle, path: path, digest: policy.digest, root: root))
            precondition(!policy.permits(bundle: "research.agentfreebrowser.fake", path: path, digest: policy.digest, root: root))
            precondition(!policy.permits(bundle: policy.bundle, path: path + ".fake", digest: policy.digest, root: root))
            precondition(!policy.permits(bundle: policy.bundle, path: "/tmp" + path, digest: policy.digest, root: root))
            precondition(!policy.permits(bundle: policy.bundle, path: path, digest: String(repeating: "0", count: 64), root: root))
        }
        precondition(PreviewAXHostPolicy.hosts.count == 2)
        precondition(PreviewAXHostPolicy.markers(in: "private text AFB-0123ABCD other text") == ["AFB-0123ABCD"])
        precondition(PreviewAXHostPolicy.markers(in: "native-input password arbitrary page text").isEmpty)
        precondition(PreviewAXHostPolicy.markers(in: "AFB-0123ABCDE AFB-0123abcd AFB-123").isEmpty)
        let owners = RendererOwnership.self
        precondition(owners.permits(hostPID: 100, rendererPID: 200, rendererPath: owners.executable, responsiblePID: 100))
        precondition(!owners.permits(hostPID: 100, rendererPID: 200, rendererPath: owners.executable, responsiblePID: 300))
        precondition(!owners.permits(hostPID: 100, rendererPID: 200, rendererPath: "/tmp/fake", responsiblePID: 100))
        print("17 preview identity, ownership, and marker checks passed.")
    }
}

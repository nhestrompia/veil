import Foundation

@main
enum RendererScopeTests {
    static func main() {
        let host: Int32 = 100
        let renderer: Int32 = 200
        for path in [RendererOwnership.executable, RendererOwnership.cryptexExecutable] {
            precondition(RendererOwnership.permits(hostPID: host, rendererPID: renderer, rendererPath: path, responsiblePID: host))
            precondition(!RendererOwnership.permits(hostPID: host, rendererPID: renderer, rendererPath: path, responsiblePID: 300))
            precondition(!RendererOwnership.permits(hostPID: host, rendererPID: host, rendererPath: path, responsiblePID: host))
            precondition(!RendererOwnership.permits(hostPID: 1, rendererPID: renderer, rendererPath: path, responsiblePID: 1))
        }
        for path in ["/tmp" + RendererOwnership.executable, RendererOwnership.executable + ".fake", "/Applications/Safari.app/Contents/MacOS/Safari"] {
            precondition(!RendererOwnership.permits(hostPID: host, rendererPID: renderer, rendererPath: path, responsiblePID: host))
        }
        let valid = "http://127.0.0.1:8765/trial/0123456789abcdef"
        precondition(RendererFixtureURL.parse(valid) != nil)
        for value in [valid + "?x=1", valid + "#x", valid + "/action", valid.replacingOccurrences(of: "127.0.0.1", with: "example.org"),
                      valid.replacingOccurrences(of: "http:", with: "https:"), valid.replacingOccurrences(of: "8765", with: "9999"),
                      valid.replacingOccurrences(of: "127.0.0.1", with: "name@127.0.0.1"), "javascript:alert(1)"] {
            precondition(RendererFixtureURL.parse(value) == nil)
        }
        print("Renderer ownership and fixture URL boundary checks passed.")
    }
}

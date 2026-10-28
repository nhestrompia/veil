import AppKit

@main
enum ResearchQuit {
    @MainActor static func main() throws {
        let arguments = CommandLine.arguments
        guard arguments.count == 2, let pid = Int32(arguments[1]),
              let target = NSRunningApplication(processIdentifier: pid) else { exit(2) }
        let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
            .deletingLastPathComponent().deletingLastPathComponent()
        guard let executable = target.executableURL,
              ResearchQuitScope.permits(bundleIdentifier: target.bundleIdentifier ?? "", executable: executable, root: root) else { exit(2) }
        let requested = target.terminate()
        RunLoop.current.run(until: Date().addingTimeInterval(0.5))
        let result = ["requested": requested, "terminated": target.isTerminated]
        let data = try JSONSerialization.data(withJSONObject: result, options: [.sortedKeys])
        FileHandle.standardOutput.write(data)
        print()
    }
}

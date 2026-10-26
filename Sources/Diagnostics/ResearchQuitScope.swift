import Foundation

enum ResearchQuitScope {
    static func permits(bundleIdentifier: String, executable: URL, root: URL) -> Bool {
        let allowed = ["research.agentfreebrowser.control": "InspectableControl",
                       "research.agentfreebrowser.internalkeyboardcontrol": "InternalKeyboardControl"]
        guard let name = allowed[bundleIdentifier] else { return false }
        let expected = root.appendingPathComponent("dist/\(name).app/Contents/MacOS/\(name)")
        return executable.resolvingSymlinksInPath() == expected.resolvingSymlinksInPath()
    }
}

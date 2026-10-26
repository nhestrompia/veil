import Foundation

@main
enum ResearchQuitScopeTests {
    static func main() {
        let root = URL(fileURLWithPath: "/research")
        func executable(_ name: String) -> URL {
            root.appendingPathComponent("dist/\(name).app/Contents/MacOS/\(name)")
        }
        precondition(ResearchQuitScope.permits(bundleIdentifier: "research.agentfreebrowser.control",
                                              executable: executable("InspectableControl"), root: root))
        precondition(ResearchQuitScope.permits(bundleIdentifier: "research.agentfreebrowser.internalkeyboardcontrol",
                                              executable: executable("InternalKeyboardControl"), root: root))
        precondition(!ResearchQuitScope.permits(bundleIdentifier: "research.agentfreebrowser.devicekeyboard",
                                               executable: executable("DeviceKeyboardExperiment"), root: root))
        precondition(!ResearchQuitScope.permits(bundleIdentifier: "research.agentfreebrowser.control",
                                               executable: executable("DeviceKeyboardExperiment"), root: root))
        precondition(!ResearchQuitScope.permits(bundleIdentifier: "research.agentfreebrowser.control",
                                               executable: URL(fileURLWithPath: "/other/InspectableControl"), root: root))
        print("Quit scope checks passed without process access")
    }
}

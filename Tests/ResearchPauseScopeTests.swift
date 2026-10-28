@main
enum ResearchPauseScopeTests {
    static func main() {
        let root = "/research"
        let host = ResearchPauseScope.hostPath(root: root)
        let content = ResearchPauseScope.contentPath(root: root)
        precondition(ResearchPauseScope.permits(root: root, hostPID: 10, hostPath: host, contentPID: 20, contentPath: content))
        precondition(!ResearchPauseScope.permits(root: root, hostPID: 10,
            hostPath: root + "/dist/DeviceKeyboardExperiment.app/Contents/MacOS/DeviceKeyboardExperiment",
            contentPID: 20, contentPath: content))
        precondition(!ResearchPauseScope.permits(root: root, hostPID: 10, hostPath: host,
            contentPID: 20, contentPath: "/System/Library/Frameworks/WebKit.framework/WebContent"))
        precondition(!ResearchPauseScope.permits(root: root, hostPID: 10, hostPath: host,
            contentPID: 20, contentPath: content + ".other"))
        precondition(!ResearchPauseScope.permits(root: root, hostPID: 10, hostPath: host,
            contentPID: 10, contentPath: content))
        precondition(!ResearchPauseScope.permits(root: root, hostPID: 1, hostPath: host,
            contentPID: 20, contentPath: content))
        print("Research pause scope passed six pure checks.")
    }
}

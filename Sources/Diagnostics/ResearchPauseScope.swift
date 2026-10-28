struct ResearchPauseScope {
    static func hostPath(root: String) -> String {
        root + "/dist/InternalKeyboardControl.app/Contents/MacOS/InternalKeyboardControl"
    }

    static func contentPath(root: String) -> String {
        root + "/.build/webkit-engine/output/Release/com.apple.WebKit.WebContent.xpc/Contents/MacOS/com.apple.WebKit.WebContent.Development"
    }

    static func permits(root: String, hostPID: Int32, hostPath: String, contentPID: Int32, contentPath: String) -> Bool {
        hostPID > 1 && contentPID > 1 && hostPID != contentPID
            && hostPath == Self.hostPath(root: root) && contentPath == Self.contentPath(root: root)
    }
}

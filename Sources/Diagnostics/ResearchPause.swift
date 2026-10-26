import Foundation
import Darwin

@main
enum ResearchPause {
    private static let root = URL(fileURLWithPath: #filePath)
        .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
        .resolvingSymlinksInPath().path

    private static func emit(_ value: [String: Any]) throws {
        let data = try JSONSerialization.data(withJSONObject: value, options: [.sortedKeys])
        FileHandle.standardOutput.write(data)
        FileHandle.standardOutput.write(Data([10]))
    }

    private static func canonical(_ path: String) -> String {
        URL(fileURLWithPath: path).resolvingSymlinksInPath().path
    }

    private static func stillMatches(_ identity: ResearchProcessIdentity) -> Bool {
        (try? ResearchProcessIdentity(pid: identity.pid)) == identity
    }

    private static func watchdog(_ arguments: [String]) throws {
        guard arguments.count == 4, let pid = Int32(arguments[1]), pid > 1,
              let seconds = UInt64(arguments[2]), let microseconds = UInt64(arguments[3]) else {
            throw RendererScopeError.unrelatedRenderer
        }
        Thread.sleep(forTimeInterval: 4)
        guard let current = try? ResearchProcessIdentity(pid: pid),
              canonical(current.path) == canonical(ResearchPauseScope.contentPath(root: root)),
              current.startedSeconds == seconds, current.startedMicroseconds == microseconds else {
            try emit(["status": "watchdog-target-gone"])
            return
        }
        let result = kill(pid, SIGCONT)
        try emit(["status": "watchdog-resume", "continueSent": result == 0, "pid": pid])
        if result != 0 { throw RendererScopeError.unavailableProcess }
    }

    private static func pause(_ arguments: [String]) throws {
        guard arguments.count == 2, let hostPID = Int32(arguments[0]), let contentPID = Int32(arguments[1]) else {
            throw RendererScopeError.unrelatedHost
        }
        let host = try ResearchProcessIdentity(pid: hostPID)
        let content = try ResearchProcessIdentity(pid: contentPID)
        guard ResearchPauseScope.permits(root: root, hostPID: hostPID, hostPath: canonical(host.path),
                                         contentPID: contentPID, contentPath: canonical(content.path)) else {
            throw RendererScopeError.unrelatedRenderer
        }
        let recovery = Process()
        recovery.executableURL = URL(fileURLWithPath: CommandLine.arguments[0]).resolvingSymlinksInPath()
        recovery.arguments = ["--watchdog", String(contentPID), String(content.startedSeconds), String(content.startedMicroseconds)]
        try recovery.run()
        defer {
            if stillMatches(content) { _ = kill(contentPID, SIGCONT) }
            recovery.waitUntilExit()
        }
        guard stillMatches(host), stillMatches(content), kill(contentPID, SIGSTOP) == 0 else {
            throw RendererScopeError.changedIdentity
        }
        try emit(["status": "paused", "stopSent": true, "hostPID": hostPID,
                  "contentPID": contentPID, "watchdogPID": recovery.processIdentifier])
        Thread.sleep(forTimeInterval: 3)
        guard stillMatches(content), kill(contentPID, SIGCONT) == 0 else {
            throw RendererScopeError.changedIdentity
        }
        try emit(["status": "resumed", "continueSent": true, "contentPID": contentPID])
    }

    static func main() {
        do {
            let arguments = Array(CommandLine.arguments.dropFirst())
            if arguments.first == "--watchdog" {
                try watchdog(arguments)
            } else {
                try pause(arguments)
            }
        } catch {
            try? emit(["status": "refused-or-failed", "error": String(describing: error)])
            exit(1)
        }
    }
}

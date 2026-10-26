import Foundation
import Darwin

struct SignalTargetSnapshot: Codable, Equatable, Sendable {
    let pid: Int32
    let path: String
    let startedSeconds: UInt64
    let startedMicroseconds: UInt64
}

enum SignalAuthorizationError: Error {
    case invalidTarget
    case invalidLifetime
    case missingPrerequisites
    case invalidArguments
    case unavailableSignature
    case connectionFailed(UInt32)
    case subscriptionFailed
    case invalidManifest
}

struct SignalAuthorizationPolicy: Sendable {
    let target: SignalTargetSnapshot
    let lifetimeSeconds: Int

    static func allowedPaths(root: String) -> Set<String> {
        [root + "/.build/signal-signing-control/ordinary",
         root + "/.build/signal-signing-control/hardened",
         root + "/.build/webkit-engine/output/Release/com.apple.WebKit.WebContent.xpc/Contents/MacOS/com.apple.WebKit.WebContent.Development"]
    }

    init(root: String, target: SignalTargetSnapshot, lifetimeSeconds: Int = 15) throws {
        guard target.pid > 1, target.startedSeconds > 0, target.startedMicroseconds < 1_000_000,
              Self.allowedPaths(root: root).contains(target.path) else {
            throw SignalAuthorizationError.invalidTarget
        }
        guard (1...15).contains(lifetimeSeconds) else {
            throw SignalAuthorizationError.invalidLifetime
        }
        self.target = target
        self.lifetimeSeconds = lifetimeSeconds
    }

    func denies(signal: Int32, target observed: SignalTargetSnapshot, elapsed: Double) -> Bool {
        signal == SIGSTOP && observed == target && elapsed.isFinite && elapsed >= 0
            && elapsed < Double(lifetimeSeconds)
    }
}

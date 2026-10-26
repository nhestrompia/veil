import Foundation
import Darwin

@main
enum SignalAuthorizationPolicyTests {
    static func main() throws {
        let root = "/research"
        let path = root + "/.build/signal-signing-control/hardened"
        let target = SignalTargetSnapshot(pid: 10, path: path, startedSeconds: 100, startedMicroseconds: 25)
        let policy = try SignalAuthorizationPolicy(root: root, target: target)
        var checks = 0
        func check(_ value: Bool) {
            precondition(value)
            checks += 1
        }
        for number in Int32(0)...Int32(32) {
            check(policy.denies(signal: number, target: target, elapsed: 1) == (number == SIGSTOP))
        }
        for elapsed in [-1.0, 15, 20, Double.infinity, -Double.infinity, Double.nan] {
            check(!policy.denies(signal: SIGSTOP, target: target, elapsed: elapsed))
        }
        check(policy.denies(signal: SIGSTOP, target: target, elapsed: 0))
        check(policy.denies(signal: SIGSTOP, target: target, elapsed: 14.999))
        let different = [
            SignalTargetSnapshot(pid: 11, path: path, startedSeconds: 100, startedMicroseconds: 25),
            SignalTargetSnapshot(pid: 10, path: path + ".other", startedSeconds: 100, startedMicroseconds: 25),
            SignalTargetSnapshot(pid: 10, path: path, startedSeconds: 101, startedMicroseconds: 25),
            SignalTargetSnapshot(pid: 10, path: path, startedSeconds: 100, startedMicroseconds: 26)
        ]
        for observed in different {
            check(!policy.denies(signal: SIGSTOP, target: observed, elapsed: 1))
        }
        for allowed in SignalAuthorizationPolicy.allowedPaths(root: root) {
            let snapshot = SignalTargetSnapshot(pid: 10, path: allowed, startedSeconds: 100, startedMicroseconds: 25)
            check(try SignalAuthorizationPolicy(root: root, target: snapshot).denies(signal: SIGSTOP, target: snapshot, elapsed: 1))
        }
        for badPath in ["/System/Library/WebKit/WebContent", root + "/dist/DeviceKeyboardExperiment.app/Contents/MacOS/DeviceKeyboardExperiment",
                        root + "/dist/NativeProbe.app/Contents/MacOS/NativeProbe", path + ".other", "/other" + path] {
            do {
                _ = try SignalAuthorizationPolicy(root: root, target: SignalTargetSnapshot(pid: 10, path: badPath, startedSeconds: 100, startedMicroseconds: 25))
                preconditionFailure("An unrelated target was accepted")
            } catch SignalAuthorizationError.invalidTarget { checks += 1 }
        }
        for pid in [Int32(-1), 0, 1] {
            do {
                _ = try SignalAuthorizationPolicy(root: root, target: SignalTargetSnapshot(pid: pid, path: path, startedSeconds: 100, startedMicroseconds: 25))
                preconditionFailure("An invalid PID was accepted")
            } catch SignalAuthorizationError.invalidTarget { checks += 1 }
        }
        for invalid in [SignalTargetSnapshot(pid: 10, path: path, startedSeconds: 0, startedMicroseconds: 25),
                        SignalTargetSnapshot(pid: 10, path: path, startedSeconds: 100, startedMicroseconds: 1_000_000)] {
            do {
                _ = try SignalAuthorizationPolicy(root: root, target: invalid)
                preconditionFailure("An invalid process start time was accepted")
            } catch SignalAuthorizationError.invalidTarget { checks += 1 }
        }
        for duration in [-1, 0, 16, 100] {
            do {
                _ = try SignalAuthorizationPolicy(root: root, target: target, lifetimeSeconds: duration)
                preconditionFailure("An unbounded lifetime was accepted")
            } catch SignalAuthorizationError.invalidLifetime { checks += 1 }
        }
        let short = try SignalAuthorizationPolicy(root: root, target: target, lifetimeSeconds: 1)
        check(short.denies(signal: SIGSTOP, target: target, elapsed: 0.999))
        check(!short.denies(signal: SIGSTOP, target: target, elapsed: 1))
        let encoded = try JSONEncoder().encode(target)
        check(try JSONDecoder().decode(SignalTargetSnapshot.self, from: encoded) == target)
        print("Signal authorization policy passed \(checks) pure checks. No ES client or signal was used.")
    }
}

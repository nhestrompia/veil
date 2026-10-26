import Foundation
import Darwin
import EndpointSecurity
import Security
import Synchronization

private struct SignalAuthorizationCounts: Sendable {
    var ownedEvents = 0
    var denied = 0
    var responseFailures = 0
}

@main
enum SignalAuthorization {
    private static let root = URL(fileURLWithPath: #filePath)
        .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
        .resolvingSymlinksInPath().path

    private static func emit(_ value: [String: Any]) throws {
        let data = try JSONSerialization.data(withJSONObject: value, options: [.sortedKeys])
        FileHandle.standardOutput.write(data)
        FileHandle.standardOutput.write(Data([10]))
    }

    private static func entitlementPresent() throws -> Bool {
        var dynamic: SecCode?
        var code: SecStaticCode?
        var info: CFDictionary?
        guard SecCodeCopySelf([], &dynamic) == errSecSuccess, let dynamic,
              SecCodeCopyStaticCode(dynamic, [], &code) == errSecSuccess, let code,
              SecCodeCopySigningInformation(code, SecCSFlags(rawValue: kSecCSSigningInformation), &info) == errSecSuccess,
              let info = info as? [String: Any] else {
            throw SignalAuthorizationError.unavailableSignature
        }
        let entitlements = info[kSecCodeInfoEntitlementsDict as String] as? [String: Any] ?? [:]
        return entitlements["com.apple.developer.endpoint-security.client"] as? Bool == true
    }

    private static func snapshot(pid: Int32) throws -> SignalTargetSnapshot {
        let identity = try ResearchProcessIdentity(pid: pid)
        return SignalTargetSnapshot(pid: pid, path: identity.path, startedSeconds: identity.startedSeconds,
                                    startedMicroseconds: identity.startedMicroseconds)
    }

    private static func snapshot(_ process: es_process_t) -> SignalTargetSnapshot? {
        guard !process.executable.pointee.path_truncated, process.start_time.tv_sec > 0,
              process.start_time.tv_usec >= 0, process.start_time.tv_usec < 1_000_000 else { return nil }
        let token = process.executable.pointee.path
        guard let path = String(bytes: UnsafeRawBufferPointer(start: token.data, count: token.length), encoding: .utf8) else { return nil }
        return SignalTargetSnapshot(pid: audit_token_to_pid(process.audit_token), path: path,
                                    startedSeconds: UInt64(process.start_time.tv_sec),
                                    startedMicroseconds: UInt64(process.start_time.tv_usec))
    }

    private static func loadPolicy(_ path: String) throws -> SignalAuthorizationPolicy {
        let url = URL(fileURLWithPath: path).standardizedFileURL
        guard url.path == url.resolvingSymlinksInPath().path,
              url.path.hasPrefix(root + "/artifacts/"), url.lastPathComponent == "signal-target.json" else {
            throw SignalAuthorizationError.invalidManifest
        }
        let attributes = try FileManager.default.attributesOfItem(atPath: url.path)
        guard attributes[.type] as? FileAttributeType == .typeRegular,
              (attributes[.posixPermissions] as? NSNumber)?.intValue == 0o600,
              (attributes[.size] as? NSNumber)?.intValue ?? Int.max <= 8192 else {
            throw SignalAuthorizationError.invalidManifest
        }
        let target = try JSONDecoder().decode(SignalTargetSnapshot.self, from: Data(contentsOf: url))
        let policy = try SignalAuthorizationPolicy(root: root, target: target)
        guard try snapshot(pid: target.pid) == target else { throw SignalAuthorizationError.invalidTarget }
        return policy
    }

    private static func run(_ policy: SignalAuthorizationPolicy) throws {
        guard try entitlementPresent(), geteuid() == 0 else { throw SignalAuthorizationError.missingPrerequisites }
        let counts = Mutex(SignalAuthorizationCounts())
        let started = ProcessInfo.processInfo.systemUptime
        var client: OpaquePointer?
        let result = es_new_client(&client) { connection, rawMessage in
            let message = rawMessage.pointee
            guard message.action_type == ES_ACTION_TYPE_AUTH else { return }
            var deny = false
            var owned = false
            if message.event_type == ES_EVENT_TYPE_AUTH_SIGNAL, message.version >= 3,
               let observed = snapshot(message.event.signal.target.pointee) {
                let event = message.event.signal
                owned = observed == policy.target
                deny = policy.denies(signal: event.sig, target: observed,
                                     elapsed: ProcessInfo.processInfo.systemUptime - started)
            }
            let response = es_respond_auth_result(connection, rawMessage, deny ? ES_AUTH_RESULT_DENY : ES_AUTH_RESULT_ALLOW, false)
            counts.withLock {
                if owned { $0.ownedEvents += 1 }
                if deny { $0.denied += 1 }
                if response != ES_RESPOND_RESULT_SUCCESS { $0.responseFailures += 1 }
            }
        }
        guard result == ES_NEW_CLIENT_RESULT_SUCCESS, let client else {
            throw SignalAuthorizationError.connectionFailed(result.rawValue)
        }
        // This finite CLI owns the client until process exit. Do not delete it
        // concurrently with an Endpoint Security response callback.
        var event = ES_EVENT_TYPE_AUTH_SIGNAL
        guard es_subscribe(client, &event, 1) == ES_RETURN_SUCCESS else {
            throw SignalAuthorizationError.subscriptionFailed
        }
        try emit(["status": "research-subscription-active", "targetPID": policy.target.pid,
                  "maximumSeconds": policy.lifetimeSeconds, "defaultMutingChanged": false,
                  "coverageVerified": false])
        Thread.sleep(forTimeInterval: Double(policy.lifetimeSeconds))
        let unsubscribed = es_unsubscribe_all(client) == ES_RETURN_SUCCESS
        let summary = counts.withLock { $0 }
        try emit(["status": "research-window-ended", "ownedEvents": summary.ownedEvents,
                  "denyResponsesAttempted": summary.denied, "responseFailures": summary.responseFailures,
                  "unsubscribed": unsubscribed, "clientLifetime": "until-process-exit", "coverageVerified": false])
    }

    static func main() {
        do {
            let args = Array(CommandLine.arguments.dropFirst())
            if args.isEmpty || args == ["--preflight"] {
                let entitled = try entitlementPresent()
                try emit(["status": "preflight-only", "endpointSecurityEntitlement": entitled,
                          "runningAsRoot": geteuid() == 0, "canAttemptConnection": entitled && geteuid() == 0,
                          "TCC": "not-tested", "clientCreated": false, "eventsSubscribed": false,
                          "enforcementVerified": false])
            } else if args.count == 2, args[0] == "--target", let pid = Int32(args[1]), pid > 1 {
                let target = try snapshot(pid: pid)
                _ = try SignalAuthorizationPolicy(root: root, target: target)
                FileHandle.standardOutput.write(try JSONEncoder().encode(target))
                FileHandle.standardOutput.write(Data([10]))
            } else if args.count == 2, args[0] == "--run" {
                try run(loadPolicy(args[1]))
            } else {
                throw SignalAuthorizationError.invalidArguments
            }
        } catch {
            try? emit(["status": "refused-or-failed", "error": String(describing: error), "enforcementVerified": false])
            exit(1)
        }
    }
}

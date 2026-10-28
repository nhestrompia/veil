# Signal authorization prototype

Milestone 90 adds a finite Endpoint Security prototype. It compiles against the installed Apple SDK and passes 65 pure policy checks. Six integration checks verify safe refusals using a fresh disposable command-line target. No Endpoint Security client, subscription, privileged service, or new permission was created.

The proposed policy denies only SIGSTOP to one exact target during a window of at most fifteen seconds. It matches the PID, executable path, and process start time. It allows SIGCONT, termination signals, unrelated processes, stale identities, and events after expiry. Its allowed paths include two disposable signing controls and the isolated custom WebKit content process. The frozen physical browser and system WebKit paths remain excluded.

The adapter reads kernel event metadata, checks the message version, rejects truncated paths, and replies without caching. It leaves Apple's default muting unchanged. It stores only counts for the selected target and response failures. A denial response is an attempted authorization decision. It is not evidence that the operating system stopped an attack.

Read-only preflight reports no Endpoint Security entitlement and no root privilege. The user also confirmed that no Apple-granted entitlement exists for this project. TCC status remains untested. The valid-target integration case therefore returns `missingPrerequisites` before connecting. Other cases reject public, oversized, stale, symlinked, and incorrectly named manifests. All six pass. The disposable target and its watchdog exit normally.

Apple documents signal authorization and requires its restricted entitlement for an ordinary client. Its client errors also identify root and TCC prerequisites. Existing Accessibility and Input Monitoring grants do not supply these requirements. [Apple signal authorization](https://developer.apple.com/documentation/endpointsecurity/es_event_type_auth_signal), [Apple entitlement](https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.developer.endpoint-security.client), [Apple client errors](https://developer.apple.com/documentation/endpointsecurity/es_new_client_result_t).

The prototype runs as a finite CLI, not an installed extension. It unsubscribes at expiry and owns the client until process exit. This avoids deleting a client while a response callback uses it. Cleanup, pending-event behavior, default muting, and coverage still require live checks after approved signing and deployment.

Before any privileged run, prepare a signed immutable helper, root-owned deployment files, a fixed target manifest, a rollback path, and explicit approval. First compare covered and uncovered disposable CLI targets. Verify the attack receives a permission error while SIGCONT and cleanup still work. Then repeat the existing browser timing attack and confirm no website action. Client failure, target replacement, expiry, and an unrelated external sender need separate controls. This milestone performs none of those live enforcement tests.

Build with `bash scripts/build-signal-authorization.sh`. That command runs pure checks and read-only preflight. Run the safe integration checks with `python3 tools/run_signal_authorization_preflight.py --output artifacts/new-signal-preflight`. The script refuses entitled or privileged execution. All 116 existing Python checks pass. [Evidence](evidence/signal-authorization-results.json) records the compiled helper identity and refusal results.

The process-pause bypass remains open. Agent-free operation remains unmet. Continue independent password-transition and browser-route tests while the entitlement prerequisite is unavailable.

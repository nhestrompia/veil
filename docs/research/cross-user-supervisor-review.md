# Cross-user supervisor review

Checked 2026-10-26. Scope: one proposed inline rendering smoke test. Root execution is not authorized. The completed milestone 98 approval cannot cover this test. The final implementation review appears below.

Use a distinct unsandboxed, pipe-only build of the milestone 101 probe for the first test. It must accept only `--pipe-only`. Remove its file-output and loopback modes from this build. Keep the fixed fixture, nonpersistent website data, inspection disabled, and activation prohibited. This tests the missing credential/session integration directly. It does not establish filesystem isolation or pause denial. [Existing pipe baseline](../renderer-pipe-findings.md).

The milestone 102 network-enabled App Sandbox variant is a later comparison. It adds successful UID-501 host write denial, but also adds an outgoing-network entitlement and unresolved `nobody` container setup. The app-sandbox-only variant fails WebKit initialization. Neither variant supplies a zero-external-write guarantee. [Measured sandbox controls](../renderer-filesystem-findings.md), [source review](renderer-filesystem-containment.md).

## Required static boundaries

| Boundary | Required check |
| --- | --- |
| Trusted launch | Root parent loads no Cocoa or WebKit. It accepts no runtime command, PID, UID, URL, script, or path. |
| Staged image | Hash the copied executable and bundle metadata. Check signature, hardened runtime, system dependencies, loader commands, ownership, links, modes, and access-control lists before execution. |
| Child access | Keep staging root-owned and unwritable by `nobody`, but readable and searchable for execution. Do not reuse root-only `0700` image permissions. |
| Credentials | Replace supplementary groups, then call `setgid`, then `setuid`. Require matching real/effective/saved IDs, allowed groups, and failed attempts to regain root. |
| Startup ordering | Root parent checks its known child's kernel identity before permitting execution. Arm and acknowledge independent cleanup first. |
| Results | Use fixed preopened pipes, a three-MiB combined output cap, and a fixed wall-clock deadline. Root treats all received bytes as opaque. |
| Signals | Every signal target comes from the supervisor's own fork records. No reported PID, process-name search, or XPC service enters cleanup. |
| Recovery | Reset inherited signal masks and dispositions. A detached watchdog must survive foreground-group interruption and outlive the parent deadline. |
| Reaping | Retain unreaped child identity and start time. Stop signaling on `ECHILD`. Resume before termination, then reap only owned children. |

Apple's privileged identity calls change real, effective, and saved IDs. Group changes must precede the UID drop. `execve` preserves open descriptors without close-on-exec and preserves blocked or ignored signals. Check the post-exec host credentials again before constructing `NSApplication`. [Apple identity calls](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/setuid.2.html), [Apple privilege ordering](https://developer.apple.com/library/archive/documentation/Security/Conceptual/SecureCodingGuide/Articles/AccessControl.html), [Apple exec contract](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/execve.2.html).

Ordinary-user controls must establish the final executable, output cap, deadline, watchdog-only recovery, and original-group interruption behavior before approval. A normal return must include direct-child reaping. An interrupted run must not claim successful rendering or complete auxiliary cleanup.

## Result and approval limits

Record the host's session context and exact content, GPU, and network PID credentials before and after the fixture. Require matching kernel real/effective/saved UID/GID for every identified role. Missing metadata is incomplete evidence. Ordinary-user result analysis may parse those records. The root supervisor must not use them as authority for any action. Pinned WebKit uses launchd XPC services, so host identity does not establish auxiliary identity. [Pinned launcher](https://github.com/WebKit/WebKit/blob/94f9b7905e3ce9a3d7497f26b563adcad6b7525f/Source/WebKit/UIProcess/Launcher/cocoa/ProcessLauncherCocoa.mm#L217).

A future approval must name the final hashes, one-run count, time/output limits, and these remaining uncertainties:

- Cocoa and XPC services can create OS-managed per-user caches outside staging.
- `nobody` is a shared existing identity, not a private account for this browser.
- The inherited GUI/security context can retain session capabilities or fail WindowServer access.
- Auxiliary services are not children this supervisor can reap. Remaining roles prevent a complete-cleanup claim.

Changing UID does not create another user's complete GUI context. No session join, account, service, privacy grant, directory ownership repair, or further administrator action belongs to the smoke test. First establish rendering and credentials. A separately reviewed pause attack can then test the actual denial boundary. [Apple execution contexts](https://developer.apple.com/library/archive/technotes/tn2083/_index.html#SECEXECUTIONCONTEXTS), [cross-user feasibility review](cross-user-renderer-feasibility-plan.md).

## Implementation review, milestone 103

The final supervisor and staging generator now implement the static boundaries above. Independent review identified two concrete defects before approval. The generator now checks the dependency tool's exit status before parsing output. Cleanup now restores access on only the known staging directories before unlinking files. Ten staging tests pass, including a partial-output failure regression. The final ordinary-user staging rehearsal passes with the exact native image hashes.

The supervisor now checks its own child's post-execution identity. The child checks its credentials before `NSApplication` initialization. WebKit role records remain app-side kernel samples. The supervisor's success field covers transport and direct-child lifecycle. Rendering success requires the separate JavaScript, pixel, and role checks.

The 32-second alarm covers the supervisor phase only. Copy and tool steps have separate alarms. The complete staging command has no single deadline. SIGKILL of the outer shell can leave fixed staging files. The watchdog protects its direct child and does not guarantee auxiliary-service or staging cleanup.

The [exact plan](../evidence/renderer-identity-reviewed-run-plan.json) remains unexecuted. Existing shared-identity, cache, inherited-session, and auxiliary-lifecycle uncertainties remain. This review supports asking for a separate one-run approval. It does not establish pause denial or agent-free operation.

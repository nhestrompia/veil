# Cross-user renderer feasibility gate

Checked 2026-10-26. Research only. The earlier root authorization is consumed. This note authorizes no execution, grant, service, or account change. No cross-user command is ready.

The smallest next experiment is one inline fixture in a disposable host after a permanent drop to `nobody`. It must test rendering and service identity before any signal attack. A launch in the caller's inherited session is a compatibility experiment. It is not a private GUI session or an agent-free browser.

## Current evidence

Three milestone 99 runs passed JavaScript and snapshot pixel checks. Three milestone 100 loopback runs passed document, iframe, image, and fetch checks. Three later inline runs also passed. All sampled host, content, GPU, and network credentials used UID 501. Each run recorded an invisible, nonkey `TUINSWindow`. Thus the current probe does not establish WindowServer independence. [Recorded inline evidence](../evidence/headless-renderer-results.json), [loopback artifacts](../../artifacts/headless-renderer-100-loopback/results.json), [inline regression](../../artifacts/headless-renderer-100-inline/results.json).

## What identity changes preserve

Apple distinguishes BSD credentials, Mach bootstrap context, and GUI security context. A process inherits its bootstrap reference from its parent. Changing UID/GID alone does not create the complete context of another user. A finite launcher can permanently drop credentials before direct `execve`. It must then measure which session survives. It must not infer GUI permission from retained context alone. Apple's archived WindowServer guidance also describes additional connection checks. Its historical details do not guarantee current behavior. [Apple execution contexts](https://developer.apple.com/library/archive/technotes/tn2083/_index.html#SECEXECUTIONCONTEXTS), [Apple identity calls](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/setuid.2.html), [Apple exec contract](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/execve.2.html).

The pinned WebKit services use `JoinExistingSession=true`. Apple defines that key as joining the caller's security session. That session can supply access to keychain, pasteboard, and other session services. The key does not guarantee matching BSD credentials or exclusive resources. The launcher must neither create nor join another security session to repair a failed test. [Apple XPC session key](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingXPCServices.html), [pinned service templates and launch trace](renderer-identity-probe-plan.md).

## Minimum contained design

The launcher needs a separate review and a fresh, hash-bound approval. It must remain a finite native supervisor. It must initialize no Cocoa/WebKit object as root. It must never use `open`, LaunchServices, `launchctl asuser`, a service install, or a credential repair route. Direct execution avoids asking LaunchServices to select an identity. The current `open -g -n` controller is unsuitable for this experiment.

1. Stage the reviewed bundle under root ownership. Check its manifest, signature, runtime flag, and absolute system dependencies after the copy.
2. Fork one host with fixed arguments. Replace its groups and permanently drop real, effective, and saved UID/GID before `execve`.
3. Run the fixed inline fixture with activation prohibited. Record credentials and session context before constructing the web view.
4. Check JavaScript, snapshot pixels, and exact content/GPU/network identities. Accept no URL, script, PID, command, or output path from an external caller.
5. Close the host within a fixed deadline. Reap only owned children and record auxiliary process exits separately.

The staged app must be readable and executable by the dropped child while remaining unwritable by it. Milestone 98's root-only `0700` executable cannot support execution after the drop. A root-owned executable tree and a separate child work directory serve different purposes. The child needs no access to this workspace. The current probe's workspace output restriction therefore needs a separate reviewed adapter. [Apple execution permission errors](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/execve.2.html).

Use preopened pipes or fixed image descriptors for results. Close other inherited descriptors. The root parent must not parse child messages as commands, signal child-reported PIDs, or follow child-reported paths. Treat report bytes as untrusted output. Retain the detached watchdog and direct-child ownership checks from the signal control. This first experiment sends no SIGSTOP. [Apple privileged-helper guidance](https://developer.apple.com/library/archive/documentation/Security/Conceptual/SecureCodingGuide/Articles/AccessControl.html).

## Filesystem and service state remain a gate

Set a fresh work directory, restrictive umask, fixed environment, and no loader overrides. Record resolved home, temporary, and cache directories after the drop. Do not assume `HOME` or `TMPDIR` redirects all framework writes. Apple's Core Foundation source can prefer the password-record home and ignore `CFFIXED_USER_HOME` in setugid contexts. Darwin also has separate per-user temporary/cache directory APIs. [Apple Core Foundation home selection](https://github.com/apple-oss-distributions/CF/blob/main/CFPlatform.c), [Apple temporary-file guidance](https://developer.apple.com/library/archive/documentation/Security/Conceptual/SecureCodingGuide/Articles/RaceConditions.html), [Darwin confstr implementation](https://raw.githubusercontent.com/apple-oss-distributions/Libc/main/gen/confstr.c).

The current unsandboxed probe cannot promise zero writes outside staging. Nonpersistent website data does not cover every framework or service cache. Shared `nobody` state can also predate this run. A future proposal must bound and disclose this uncertainty or establish stronger filesystem containment first. Do not repair failures with broad directory ownership changes or grants.

## Identity and cleanup verdicts

Read kernel real/effective/saved UID/GID, start time, and executable path for the host and each exact private role getter. Compare session information before and after initialization. Require no root or UID-501 WebKit role. Missing metadata or a role restart makes identity coverage incomplete. XPC launches use `launchd`, so parent PID cannot establish ownership. The pinned network getter can itself create a service. [Pinned identity probe source plan](renderer-identity-probe-plan.md).

Sampled identities do not cover every transient process or future website. A later general claim needs process-launch tracking, replacement coverage, and independent signal tests. Auxiliary XPC services are not direct children that this launcher can reap. Wait for their measured exits. Do not terminate services by name or trust reported PIDs for privileged cleanup. Any remaining service prevents a complete-cleanup claim.

A successful result would establish one cross-user inline rendering control in one measured session. WindowServer access, retained session capabilities, shared account state, and auxiliary lifecycle are the critical feasibility questions. General websites, physical input, protected presentation, and an unpausable user-side UI remain separate work.

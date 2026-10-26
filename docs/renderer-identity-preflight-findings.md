# Renderer identity preflight

Milestone 103 prepares one cross-user rendering experiment. All ordinary-user controls pass. No administrator run occurs in this milestone. The browser remains vulnerable to the confirmed same-user pause attack.

The next test asks whether WebKit can render the fixed inline fixture after a permanent drop to the existing `nobody` identity. The earlier signal test showed kernel denial across those identities. It did not establish a working renderer under that identity. This experiment addresses that missing integration.

## Implemented boundary

A separate `RendererIdentityProbe.app` accepts only `--pipe-only`. It accepts no URL, script, output path, or network port. It uses nonpersistent website data and disables inspection. It creates no explicit window and requests no privacy grant. The frozen physical browser and permissioned probes remain unchanged.

The native supervisor loads only libSystem. It accepts a fixed mode, with no runtime process ID, user identity, command, or path. Administrator mode requires a private, root-owned staged image. The staging command copies exactly four known files through checked descriptors. It rejects symlinks, nonregular files, multiple links, shared write access, unexpected owners, and size changes. Hash, signature, hardened-runtime, dependency, and loader checks precede execution.

The supervisor replaces supplementary groups and permanently drops its renderer child to `nobody` before AppKit or WebKit initialization. It checks real, effective, and saved identities and failed attempts to regain root. The parent checks its own child's kernel identity before execution and samples it again afterward. The app independently checks its credentials before constructing `NSApplication`.

A detached watchdog acknowledges readiness before the renderer can execute. It signals only the supervisor's fork-created child, with start-time and identity checks. The supervisor never treats renderer-reported service identifiers as privileged signal targets. Root relays child output as opaque bytes. Ordinary-user analysis checks the rendering report separately.

The child output cap is three MiB. The supervisor phase has a 32-second alarm. Copying has a separate ten-second alarm. Each signature or loader tool has an eight-second alarm. The complete staging command has no single deadline. Its fixed cleanup removes only the known files and directories.

## Measured controls

Three fresh ordinary-user renderers pass JavaScript, image pixels, stable role identities, and direct-child cleanup. A fourth succeeds with inherited blocked and ignored alarm/child signals. All measured host and WebKit roles still use user ID 501. These controls establish the supervisor integration under the current user, not cross-user rendering.

The watchdog resumes and terminates its stopped disposable child. Separate controls enforce the output cap and deadline. Recovery also succeeds after a foreground-group termination, parent-only SIGKILL, and a closed output pipe. Those tests use only disposable research processes. Four invalid or unprivileged invocations refuse with exit code 64.

Ten staging tests pass. They cover valid copying and refusals for links, FIFO input, shared writes, size changes, and unsafe directory permissions. A regression supplies correct-looking dependency output followed by failure. The generated command refuses before the helper executes. This fixes a pipeline that previously could hide the dependency tool's exit status.

A final unprivileged rehearsal copies, hashes, verifies, seals, and removes the exact candidate image. Its only staging difference is the expected directory owner. Administrator mode still refuses with exit code 64. Native artifact hashes match the earlier full preflight. No measured supervisor or probe remains. All five frozen executable hashes match.

Earlier failed staging rehearsals remain in the artifacts. One exposed cleanup failure after sealing directories to mode 0555. Cleanup now restores mode 0700 on only its known directories before removing files. Another exposed Perl taint-mode environment rejection. The fixed wrappers set their own system path.

## Approval and interpretation

The exact proposed command and image manifest are in the [committed run plan](evidence/renderer-identity-reviewed-run-plan.json). The artifact copy is `artifacts/renderer-identity-103-reviewed-candidate/reviewed-run-plan.json`. Its command SHA256 is `cb83839d03e5b387967ea13a22c887bd26c264a3bf5fccd992785e197d17fc04`. Neither copy authorizes execution.

The milestone 98 administrator approval covered one completed signal test. It does not cover this new renderer run. A new approval must cover exactly one staged inline smoke test. It creates no account, service, session join, browser grant, or input hook. It performs no privileged pause attack.

Frameworks can create OS-managed caches outside staging. `nobody` is a shared identity. The inherited GUI and security context can retain capabilities or prevent rendering. WebKit role identities are app-side kernel samples, not continuous independent attestation. Auxiliary services are not children the supervisor can reap. Their complete exit remains a separate check.

SIGKILL of the outer staging shell can leave its fixed root-owned files. The detached watchdog protects the direct renderer child, not staging cleanup. Cleanup after such interruption can need another explicit administrator approval. This plan supplies no general-purpose privileged cleanup command.

A successful smoke test would establish only rendering and sampled identities for this fixed page. The next gate would test pause denial across every relevant process. Browser integration, controller protection, website compatibility, and the remaining observation/action channels would still need evidence. Agent-free operation remains unmet.

See [preflight evidence](evidence/renderer-identity-preflight-results.json) and [supervisor review](research/cross-user-supervisor-review.md).

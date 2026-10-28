# Cross-user metadata reader repair

Milestone 107 fixes a deterministic cross-user limitation in the ordinary-user signal probe. It runs no administrator command. The actual old reader fails a readonly foreign-user regression. The repaired reader passes that regression, three fresh same-user signal comparisons, and independent recovery.

The capability comparison reads only itself, its own disposable child, and system init PID 1. It sends no signals to system processes and reads no UI, command arguments, or page content. The original BSD-info API returns zero bytes and EPERM for init. The executable-path query succeeds. KERN_PROC_PID also succeeds and supplies credential, start-time, and state fields. Self and owned-child records agree across the two credential APIs.

This identifies a blocker in the old reader. It does not establish the exact failing operation in milestone 106, which recorded only a generic refusal. The earlier run remains inconclusive. See [the primary-source review](research/cross-user-metadata-review.md).

## Implemented checks

The actor uses the installed SDK's `struct kinfo_proc` and requires the exact returned size and requested PID. It checks the group count, positive start seconds, and microsecond bounds before converting fields. It preserves all six real, effective, and saved user/group checks.

Each lookup reads kernel metadata, reads the executable path, then reads kernel metadata again. Both identity samples must agree. The actor retains the exact host and role paths and its immediate pre-signal identity checks. It rejects stopped and zombie states before signals. Its independent recovery watchdog remains unchanged.

A failed initial lookup now reports the role, operation, error, byte count, and zero signal calls. The ordinary observer preserves these refusals as inconclusive results. It does not interpret failed validation as protection.

The native regression exercises the real actor reader. It fails before the repair and passes afterward. It also checks same-user parity, init credentials, and invalid or missing process refusals. Fifteen Python observer/refusal tests and eleven staging tests pass. The exact final actor passes twelve same-user pauses/resumes and a parent-death recovery trial. Every measured fixture process exits.

These metadata interfaces are diagnostic tools. Apple labels the sysctl process nodes SPI. They do not establish a stable production security contract. Reads and signals are separate operations, so the checks cannot atomically exclude every PID or execution race. Init readability does not establish WebKit-role readability. A future live lookup can still refuse.

## Proposed bounded comparison set

The [new reviewed plan](evidence/renderer-metadata-reviewed-run-plan.json) permits at most three serial comparisons if the user approves. Each administrator-command invocation consumes one attempt, including staging failure. Rendering, actor outcomes, measured process exits, and staging removal must pass before another launch. Any failure, inconclusive result, unexpected signal success, or uncertain cleanup stops the set. No retry after a code change belongs to this approval.

The administrator command and four staged images remain byte-identical to milestone 106. Only the ordinary-user actor and observer change. The per-launch command SHA256 is `22f91657b4576912489eee95c9831c68e6b24842c9d738efe81c16d51cdd3d06`. The repaired actor SHA256 is `05b0351b6352779a14d3955052b47441fbb9e74060eb5c7ab03596c168daccd0`.

Root remains limited to verified staging, the fixed inline renderer after its drop to nobody, its own-child watchdog, and fixed cleanup. Root never acts on reported service identifiers. No account, service, grant, input hook, or session repair changes. The 32-second alarm applies to each supervisor phase, not the entire set. Cache, shared-account, inherited-session, auxiliary-lifecycle, and interrupted-staging limits remain.

The milestone 106 approval covers only its completed attempt. The comparison set remains unexecuted and needs fresh approval. The browser's pause bypass, controller isolation, post-attack website progress, input, presentation, and general compatibility remain open. The browser is not feature-complete or agent-free.

See [saved controls](evidence/renderer-metadata-results.json) and [the previous inconclusive attempt](renderer-signal-results-findings.md).

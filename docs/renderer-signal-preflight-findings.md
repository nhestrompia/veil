# Renderer signal controls

Milestone 105 calibrates an ordinary-user signal actor and prepares the next cross-user experiment. Three fresh reference trials pass. Each pauses and resumes the exact host, content, GPU, and network processes from its disposable renderer. All twelve pauses produce a measured stopped state. All twelve resumes restore a nonstopped state with matching identities.

The actor uses user ID 501. It refuses root execution. It accepts no command, URL, script, arbitrary user identity, or executable path. The controller supplies process identifiers and start times from the fresh probe's role getters. The actor independently checks kernel credentials, executable paths, start times, and distinct targets before sending any signal. These checks do not independently attest role ownership. That association comes from the exact probe report.

The actor installs no input hooks and sends no keyboard or pointer input. It holds each successful reference pause for 100 milliseconds. Its detached watchdog acknowledges readiness before any pause. Killing the actor after its first observed stop triggers independent recovery. The supervisor then receives normal host exit and reaps its own children. Every reference and recovery trial leaves no measured process.

Fourteen observer and refusal tests pass. Eleven staging tests also pass. The observer waits through private staging, accepts only the fixed published report, and checks readonly app hashes. It refuses links, FIFO input, unexpected metadata, a changed image, failed rendering, and duplicate reports. It never opens the root-only supervisor. Root staging verifies that helper's bytes. A regression checks this distinction.

## Correct signal verdicts

Pause prevention requires SIGSTOP denial. SIGCONT permission has a separate verdict. Apple XNU allows continuation within one POSIX session before its ordinary user-identity comparison. The actor records both session identifiers. It accepts a documented same-session continuation success without calling it a pause bypass. Mandatory access-control policy can impose further restrictions. The installed kernel still needs a live measurement. See [the source review](research/renderer-signal-permission-review.md).

A process-state sample excludes stopped and zombie states. It does not establish website progress. The fixed page's JavaScript and image controls precede the attacks. This experiment measures signal permission, sampled identities, recovery, and host lifecycle. A later action fixture must test post-attack page progress and accepted actions.

## Prepared one-run proposal

The [exact proposed plan](evidence/renderer-signal-reviewed-run-plan.json) reuses the unchanged milestone 103 supervisor and renderer images. Its command SHA256 is `22f91657b4576912489eee95c9831c68e6b24842c9d738efe81c16d51cdd3d06`. Its ordinary-user actor SHA256 is `4220daf1f76bab892e6cb26d17fcccc4e35931da7199d881eb1544a6047202cf`.

Root would stage those same four files and launch one fixed inline renderer as nobody. It would also create one fixed readonly observation file inside staging. The ordinary-user observer would read the fixture report during its two-second hold. The actor would then attempt SIGSTOP and SIGCONT against the exact reported host and three roles. Root would never signal reported service identifiers. Its existing cleanup would remain limited to its own forked child and fixed staging files.

The observation file opens exclusively while staging is private. Its write descriptor stays open before the file becomes readonly. The supervisor receives that descriptor only as its output destination. Its renderer child closes extra inherited descriptors before execution. After the helper returns, the shell closes the descriptor, replays the fixed log, and removes the known files.

The final unprivileged staging rehearsal passes signature, hash, permission, and cleanup checks. Administrator mode refuses with exit code 64. The observer is not a privileged helper. The original smoke command remains byte-identical when observation is disabled. All frozen browser and probe hashes match.

No new administrator command runs in this milestone. The milestone 104 one-run approval covers only its completed smoke test. This proposal needs separate approval for one launch. It includes no automatic retry, new account, service, privacy grant, session repair, or input hook.

The 32-second deadline covers the supervisor phase. Copy and verification tools have separate alarms. The complete staging command has no single deadline. Framework caches, shared nobody state, inherited session capabilities, auxiliary replacements, and staging residue after outer-shell SIGKILL remain limits. The known browser pause bypass remains open.

See [reference and recovery evidence](evidence/renderer-signal-preflight-results.json) and [the rendering result](renderer-identity-results-findings.md).

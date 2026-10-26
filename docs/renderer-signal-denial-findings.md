# Cross-user renderer signal denial

Milestone 108 completes the three approved serial comparisons. The ordinary-user actor attempts SIGSTOP against the exact renderer host, content, GPU, and network processes. All twelve attempts return minus one with EPERM. The twelve SIGCONT attempts also return EPERM. No measured target enters a stopped state. All actor identity samples remain stable.

The attacker uses user ID 501. Each renderer host permanently drops to the existing nobody user before AppKit and WebKit initialization. Kernel records show real, effective, and saved user/group IDs of 4294967294 for all four roles. Three earlier same-user comparisons calibrated twelve successful stops and resumes with this same actor image. The current result establishes signal denial for the measured cross-user roles.

All three inline rendering controls pass JavaScript and image samples. Each snapshot measures 1600 by 1200 pixels and contains the expected red, green, blue, and white regions. The renderer reports no visible window. The legacy `same-user-inline` mode names the fixture. The credential fields establish the actual cross-user identity.

Each helper exits zero. Each supervisor reaps its host and watchdog. Ordinary-user checks find none of the fifteen measured process identifiers after cleanup. All three staging directories disappear. A final check confirms all five frozen browser/probe hashes and every approved command, staged image, actor, and ordinary source hash. The controller remains user ID 501.

## Authorization and scope

The user approved at most three serial invocations, stopping after any failed or inconclusive result. All three pass, and no fourth invocation occurs. The administrator command SHA256 remains `22f91657b4576912489eee95c9831c68e6b24842c9d738efe81c16d51cdd3d06`. The actor SHA256 remains `05b0351b6352779a14d3955052b47441fbb9e74060eb5c7ab03596c168daccd0`.

Root handles verified staging, its fixed nobody renderer, its own-child watchdog, and fixed cleanup. It never signals reported service identifiers. No account, service, privacy grant, input hook, or session repair changes. The first invocation waits for direct macOS authentication before staging. The user confirms authentication, then the serial batch completes. That wait does not belong to the supervisor's 32-second deadline.

All three invocation allowances are consumed. This approval permits no later administrator run or changed-image retry. Future privileged experiments need a separate concrete scope.

## What remains open

The fixture report precedes the signal attempts. Sampled non-stopped state does not prove post-attack page progress. This set does not load arbitrary websites or test physical human use. The metadata reader uses diagnostic SPI, and separate metadata and signal operations do not form an atomic process handle.

The shared nobody identity remains a research limitation. Framework caches and inherited session capabilities remain outside this result. Auxiliary identity samples do not establish continuous ownership. Interrupted outer staging can still leave files, although every measured run cleans up normally.

The ordinary browser does not integrate this identity boundary. Its same-user renderer pause bypass remains open. The next gate needs continued page progress after a calibrated pause attack. Controller isolation, private input and presentation, and broader website compatibility also remain open. The browser is not agent-free or feature-complete.

See [saved results](evidence/renderer-signal-denial-results.json), [snapshot](evidence/renderer-signal-denial-snapshot.png), and [the reviewed comparison plan](evidence/renderer-metadata-reviewed-run-plan.json).

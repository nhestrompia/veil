# Identity signal results

Milestone 98 completed the one approved administrator experiment. The exact reviewed binary and command hashes match the saved plan. The launcher exited with code zero.

The same-user actor and target used user ID 501. SIGSTOP succeeded, the parent observed the stopped child, and an explicit resume restored its heartbeat.

The cross-user target used the existing nobody identity, user ID 4294967294. The actor used user ID 501. Kernel records confirmed real, effective, and saved credentials after permanent drops. Its SIGSTOP returned EPERM. The target never entered a stopped state and answered after 0.111 seconds. That answer preceded any parent recovery signal and the watchdog's two-second recovery limit.

All children exited. The helper removed its protected temporary directory. An independent check found no staged executable process or remaining directory. Later commands ran as user ID 501. Frozen browser and probe hashes match.

This result supports the measured cross-user signal boundary for disposable command-line children. It does not establish WebKit service identities, browser rendering, physical input, or protection across websites. The browser's confirmed pause bypass remains open.

The administrator authorization covered this single test and is consumed. No further privileged command is authorized. The next experiment uses a separate same-user rendering probe without a window or permission changes.

See [measured evidence](evidence/identity-signal-results.json), [prepared controls](identity-signal-findings.md), and [renderer probe plan](research/renderer-identity-probe-plan.md).

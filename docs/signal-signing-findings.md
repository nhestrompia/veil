# Hardened Runtime signal control

Milestone 89 confirms external pause/resume in two disposable command-line controls on macOS 26.6. One control uses ordinary ad hoc signing. The other adds Hardened Runtime with no exception entitlements. Signature verification and runtime-flag checks passed before launch.

| Signing | Resume method | Observed maximum gap | Result |
| --- | --- | ---: | --- |
| Ordinary | Controller | 1.029 s | Paused and resumed |
| Ordinary | Independent watchdog | 2.737 s | Paused and resumed |
| Hardened Runtime | Controller | 1.013 s | Paused and resumed |
| Hardened Runtime | Independent watchdog | 2.738 s | Paused and resumed |

The controller sends SIGSTOP only to its own newly launched child after checking the exact executable path. It then verifies the stopped process state. In the normal trial, it sends SIGCONT after one second. In the recovery trial, it withholds resume. The target's separate watchdog sends SIGCONT after three seconds. The watchdog checks the target path and original process start time first.

Each target completes its four-second observation and waits for its watchdog. All four targets and their watchdogs exited successfully. The test adds no permission, input hook, privileged service, browser modification, or engine change.

A fresh repeat reproduced all four outcomes. Across both runs, four Hardened Runtime trials and four ordinary-signing trials observed the external pause. Every target and watchdog passed cleanup. The final controller also refuses to rebuild a control while that exact executable is running.

This is a process control, not a website or physical-human test. It shows that Hardened Runtime alone does not deny the measured same-user signal operation. It does not establish the behavior of a fully hardened browser, a particular sandbox profile, or a privileged enforcement service. Keep those distinctions separate from the six website actions in [milestone 88](engine-process-pause-findings.md).

The current engine still lacks a signal-denial boundary. An ordinary signing change cannot supply that boundary based on this control. Endpoint Security remains a separate design that needs an Apple-granted entitlement, privileged deployment, user approval, and coverage tests on this Mac. No such service is installed. See the [process-signal research](research/process-signal-boundary.md).

Run `python3 tools/run_signal_signing_control.py --output artifacts/new-signing-control` with a fresh output path. The script builds only workspace command-line fixtures. [Saved evidence](evidence/signal-signing-control-results.json) contains signature output, binary hashes, stopped-state observations, watchdog receipts, timing gaps, and cleanup results. The existing 116 Python checks remain the unit-test baseline.

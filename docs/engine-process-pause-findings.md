# Content-process pause findings

Milestone 88 confirms a process-signal bypass in the isolated engine diagnostic. Two normal pause/resume comparisons each produced one website action in native mode and one in stable mode. A separate watchdog-recovery comparison produced the same result. Every cycle admitted zero keyboard events.

The page first completes one private startup task. It then measures ten timer intervals and records an adaptive threshold. Each trial requires three stationary seconds with no new action or admitted input. Only then does an external helper pause the verified content process. The ordinary cycle resumes it after three seconds. A separate watchdog sends resume after four seconds.

| Experiment | Native gap | Stable gap | New actions per mode |
| --- | ---: | ---: | ---: |
| Watchdog recovery | 4,093 ms | 4,026 ms | 1 |
| Normal cycle 1 | 3,018 ms | 3,030 ms | 1 |
| Normal cycle 2 | 3,029 ms | 3,032 ms | 1 |

The recovery test kills only the controller's helper child after its pause receipt. Its independent watchdog resumes the exact renderer. All six renderers returned to a running state. All six disposable apps passed cleanup. Secure Event Input was off after every trial. Framework identity checks passed for each UI and content process.

The helper accepts only the InternalKeyboardControl host path and the custom WebKit content path. The controller obtains the content PID from the diagnostic's own verified engine receipt. The helper checks paths and process start times before signals. This scope is a test safeguard, not a security boundary against a malicious same-user program. Six pure tests reject unrelated paths, the physical browser, system WebKit, and invalid PIDs. No live negative test targeted those processes.

The tested host and content executables use ad hoc signatures without Hardened Runtime. These results do not measure the frozen physical browser or prove a release-signing result. They do establish that the current engine projection leaves the timer route open. Stable activity and cleared visual-idle state cannot hide this measured process interruption.

A signal handler cannot supply the missing denial boundary for SIGSTOP. See the [process-signal research](research/process-signal-boundary.md). A host watchdog may restore availability, but the measured recovery still triggers the page action. Clock changes would need separate compatibility and adaptive tests across other clocks, workers, media, network responses, and server time. They are not an implemented repair.

The current browser remains agent-resistant research. Agent-free operation across all websites remains unmet. [Saved evidence](evidence/engine-process-pause-results.json) contains the six action results, stationary controls, recovery receipts, framework identities, signing flags, and cleanup checks.

Reproduce with `bash scripts/build-research-pause.sh`, then `python3 tools/run_engine_timer_attack.py --output artifacts/new-pause-run --active-animation --intervention pause`. Use a fresh output path and the existing local feature controller. The recovery variant uses `--intervention pause-recovery`. All 116 Python checks pass.

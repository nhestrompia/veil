# Independent timing channels

Milestone 96 reproduces sixteen externally triggered website actions across four timing sources. Every source succeeds twice in each engine mode. Agent-free operation remains unmet.

| Timing source | Native actions | Stable actions |
| --- | ---: | ---: |
| Main-page performance clock | 2 of 2 | 2 of 2 |
| Main-page wall clock | 2 of 2 | 2 of 2 |
| Dedicated-worker performance clock | 2 of 2 | 2 of 2 |
| Separate server clock | 2 of 2 | 2 of 2 |

Each fresh candidate completes one private startup task. The selected detector then collects ten baseline intervals and records an adaptive threshold. Three stationary seconds produce no new action or admitted input. The existing scoped helper pauses the verified custom-engine renderer, resumes it, and confirms independent watchdog recovery. All sixteen interventions verify. Each produces exactly one new accepted task with zero admitted input events. Measured triggering gaps range from 3,013 to 3,095 milliseconds.

The fixture uses `performance.now()`, `Date.now()`, a dedicated worker, or JSON timestamps from a separate loopback server. The server clock belongs to the controller process, outside the suspended renderer. Its endpoint requires a valid disposable trial, sends no controller key or marker, and changes no task state. Responses disable caching. The controller closes this temporary server after the run. The original fixtures remain active and unchanged in process identity.

A separate server-clock pilot also succeeds once per mode. Its two actions remain separate from the sixteen-case matrix. UI and content framework identity checks pass throughout. Every temporary browser exits and aggregate Secure Event Input returns to off. The frozen browser and probes remain unchanged.

These results identify additional timing channels. They do not test a clock patch or establish that every possible patch fails. A change limited to the main page's performance clock leaves wall time and server response data outside that change. Any broader engine clock policy needs consistent scheduling, workers, animation timestamps, security deadlines, and normal elapsed-time behavior. See the [primary-source feasibility review](research/agent-free-feasibility-boundary.md).

The existing prevention verifier receives the eight stable-mode cases with their successful native controls. It must report `failed`. A successful pause action takes precedence over negative input results. Do not convert successful cleanup or zero admitted input into a prevention claim.

The separate hide/restore regression preserves the earlier result. The native control records an action, while stable mode records none. Both controls pass calibration and cleanup. The timing refactor therefore retains the measured benefit of stable activity for that route. It does not repair process suspension.

The fixture JavaScript passes syntax checking. All 141 Python checks pass, including the server endpoint and a deliberately failed controller that must retain its error and close its fixture. These checks establish test infrastructure behavior, not agent prevention.

Reproduce with `python3 tools/run_clock_channels.py --output artifacts/new-clock-channels --repetitions 2`. The command starts a temporary loopback fixture and attacks only disposable research renderers. It installs no service, requests no grant, and creates no input hook. [Evidence](evidence/clock-channel-results.json) preserves the pilot, repeated matrix, framework identities, intervention receipts, oracle outcomes, and cleanup. [Prevention input](evidence/clock-channel-prevention.json) is compatible with `tools/verify_results.py`.

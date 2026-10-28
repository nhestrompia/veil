# Direct execution and result-pipe findings

Milestone 101 adds an inline-only result transport to the separate headless diagnostic. The probe accepts no URL, script, output path, or network port in this mode. It returns its fixed control report and PNG through stdout. It still refuses execution as root.

Three direct-execution trials pass JavaScript, snapshot, stable identity, and cleanup checks. These launches use the executable directly, without LaunchServices. Each returns a 37,593-byte PNG and records zero explicit snapshot-file writes. The ordinary-user controller saves the image after receipt. Kernel records again show real, effective, and saved user ID 501 for the host and every sampled WebKit role.

The native image limit is two MiB before base64 conversion. The controller stops the stream above three MiB and enforces a 30-second deadline. Four subprocess tests cover the exact byte limit, excess data before EOF, a silent stream, and EOF without process exit. All pass. Every test child exits during cleanup. Three further renderer trials pass through this bounded reader.

A separate loopback regression also passes. The combined pipe/network option refuses before creating an output directory. All measured probe and service PIDs disappear. Frozen browser and permissioned probe hashes match. No privileged command or grant change occurs.

Zero explicit snapshot-file writes does not mean zero framework writes. The unsandboxed host and its XPC services can use OS-managed state. This result does not establish filesystem isolation, another user identity, or protection from process suspension. A hostile agent can still pause a same-user controller or renderer.

The cross-user review identifies unresolved GUI session, cache, shared-account, and auxiliary cleanup questions. No privileged renderer command is ready. The prior administrator approval covered only the completed milestone 98 signal experiment. Do not reuse it for rendering. A later proposal needs trusted staging, permanent credential drops before execution, measured role identities, and an independent watchdog.

Run `bash scripts/build-headless-renderer-probe.sh`, then `python3 tools/run_headless_renderer_probe.py --pipe --out artifacts/headless-pipe-new`. The output directory must not exist. Run `python3 -m unittest discover -s tools -p test_headless_renderer_pipe.py` for the receiver checks.

See [saved pipe results](evidence/renderer-pipe-results.json) and [cross-user feasibility review](research/cross-user-renderer-feasibility-plan.md). Agent-free operation remains unmet.

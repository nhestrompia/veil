# Post-attack page progress calibration

Milestone 110 adds a separate progress diagnostic. One baseline and three ordinary-user attack references pass. Each reference pauses and resumes the host, content, GPU, and network roles. The page then completes a fresh JavaScript challenge, updates the DOM, advances its timer, and redraws the canvas from blue to yellow. These are recovery controls, not prevention results.

The probe first renders its fixed inline page and records the role identities. It emits a readiness report without image bytes. A separate ordinary-user actor then checks exact paths, credentials, start times, and process states before each signal. Its detached recovery watchdog retains the earlier bounded design. A compile flag restricts this actor to the new progress app. The earlier actor binary remains unchanged.

Three seconds after readiness, the host creates a fresh challenge. JavaScript waits for a timer, stores the challenge in the DOM, and changes the canvas. The host then takes a fresh snapshot and records the role identities again. The controller compares CLOCK_MONOTONIC nanoseconds from both processes. The sample must start strictly after the actor finishes. All three references satisfy that order. A slow actor makes the result fail rather than weakening the ordering rule.

All twelve pauses enter the stopped state and all twelve resumes recover. Every reference passes seven acceptance checks. The document nonce, fresh DOM challenge, timer increase, yellow pixel, and final role identities match. All sixteen measured host and service identifiers exit across the baseline and three references. The actors report reaped recovery watchdogs.

Thirteen acceptance tests reject early samples, equal timestamps, stalled timers, changed documents, missing DOM updates, uncalibrated pauses, changed role identities, bad snapshots, missing roles, duplicate roles, and unreaped watchdogs. Fifteen existing observer tests, eleven staging tests, and five pipe-reader tests also pass. The native readonly metadata regression passes. Seven malformed invocations refuse before app startup or signal calls.

The new app and actor compile with warnings as errors and retain hardened runtime signatures. The five permissioned binaries, four earlier root images, and earlier signal actor retain their hashes. No administrator command, privacy grant, input hook, or global setting changes. The new app uses only its fixed inline fixture and accepts only the pipe-only argument.

This result proves post-attack progress in the same-user reference. It does not establish progress under cross-user isolation. It does not measure continued network requests, workers, arbitrary websites, or physical human use. Timer samples and one redraw do not prove uninterrupted execution. The ordinary browser still has the confirmed pause bypass.

Next, prepare the same progress measurement for the cross-user renderer. A new privileged experiment needs its own exact reviewed command and approval. The earlier three-invocation authorization is consumed. Browser integration, the control channel, physical pointer input, privacy gaps, and general website compatibility remain open.

See [saved evidence](evidence/renderer-progress-control-results.json) and [the post-attack snapshot](evidence/renderer-progress-control-snapshot.png). To reproduce, run `bash scripts/build-renderer-progress-control.sh`, then `python3 tools/run_renderer_progress_control.py --out artifacts/renderer-progress-new`. Use a new output directory.

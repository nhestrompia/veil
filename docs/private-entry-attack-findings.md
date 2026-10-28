# External input during private-entry sessions

Milestone 93 blocks 27 calibrated external input attempts across nine disposable editors and frames. All 27 readable references complete their tasks. Every candidate completes its private startup task, then admits zero external input events and records no new accepted task.

The matrix covers forms, textareas, editable content, open and closed shadow roots, SPA content, same-origin frames, cross-origin frames, and srcdoc frames. Each surface receives three routes: ordinary HID-state events, curved-pointer HID events, and PID-directed keys with virtual keycodes.

The new diagnostic has a separate external-only mode. It types its startup control once, starts a ten-second private-entry session, and schedules no further private typing. Each route uses a fresh candidate after its matched reference. This prevents authorized diagnostic tasks from becoming apparent agent successes.

The controller requires aggregate protection before and after the attempt. It checks the native window's wall-clock marker against both wall and monotonic elapsed time, uses a one-second deadline margin, and rejects a negative result if the lease ended or private typing overlapped. Posting errors, failed controls, and missing refusal evidence remain inconclusive. A new action still counts as a bypass when a protection window expires.

Every attempt passes these active-window checks. Every candidate later reports expiry, returns aggregate protection to off, and passes cleanup. Each final oracle state contains only its original private startup task. UI and content framework identity checks pass for every candidate. The preliminary one-route pilot also passes and remains separate from the 27-case matrix.

The existing device gate participates in every refusal. This experiment verifies that the session owner preserves that behavior. It does not isolate Secure Event Input as the cause, establish physical-human origin, test every observer, or prove resistance on arbitrary websites. The confirmed process-pause route remains open. The broader capture, inspection, session-reuse, and recovery requirements remain separate.

All 130 Python checks pass. The frozen browser and probes retain their existing build identities. No new grant, modifying global hook, hardware reader, or privileged service was added. [Evidence](evidence/private-entry-attack-results.json) includes calibration outcomes, active-window receipts, posting results, refusal counts, oracle outcomes, engine identities, expiry, and cleanup.

Run `python3 tools/run_private_entry_attacks.py --output artifacts/new-private-entry-attacks` with a fresh output path. The command builds the external-only diagnostic. Restore the ordinary diagnostic before later experiments with `bash scripts/diagnose-browser-keyboard.sh --build-only --feature-suite --capture-restricted --owner-readback --engine-stable`.

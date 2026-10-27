<img src="assets/icon.svg" width="64" height="64" alt="">

# agentfreebrowser

A macOS-only research project for an agent-resistant browser, with agent-free browsing as the stronger research goal.

The current candidate remains vulnerable to renderer suspension. Sixteen calibrated trials complete website actions across four clock sources in native and stable engine modes. The prevention gate fails. Earlier stable hide/restore results remain bounded to that route. Agent-free operation remains unmet. See [timing results](docs/clock-channel-findings.md) and [feasibility research](docs/research/agent-free-feasibility-boundary.md).

Start with the [proof-of-concept PRD](PRD.md). It defines the target, proposed architecture, MVP requirements, attack tests, and acceptance gates.

Supporting evidence:

- [Antiagent review](docs/research/antiagent-review.md): what worked, what failed, and which test methods to reuse.
- [Browser feasibility research](docs/research/browser-feasibility.md): official sources for inspection, accessibility, screen capture, native input, and session handling.
- [Mouse-behavior experiment](docs/research/mouse-behavior-experiment.md): physical trajectories, human-trace replay, adaptive attacks, and false blocks.
- [Protected-rendering experiment](docs/research/protected-rendering-experiment.md): a separate track for interactive HTML and capture-protected graphics paths.

The initial AppKit and WKWebView shell is implemented. See [implementation milestones](docs/implementation.md) for build commands and verification. The first experiments test native input. A resistant MVP needs measured benefits and explicit limits. The stronger agent-free claim requires separate prevention results for accessibility, capture, and native input.

The local Antiagent review checks saved evidence. The online report reviews primary sources. Neither constitutes a live test of this proposed browser.

Live prototype results:

- [Native input](docs/native-input-findings.md): five working CGEvent adapters completed all 15 protected-browser trials.
- [Capture and automation](docs/capture-findings.md): screenshot/OCR/native input completed 3/3 protected-browser trials. Playwright transport failures remain separate from protection evidence.
- [Source-state filter](docs/input-filter-findings.md): a basic client stopped, but generated HID-state input and the vision client still completed tasks.

The default browser remains an automation control and does not meet either MVP resistance gate. The latest candidate is `DeviceKeyboardExperiment.app`. It supports this Mac's measured built-in keyboard and US ASCII. Pointer input is disabled. It checks kernel device ancestry before binding and refuses known software sources or unknown paths. Its Input Monitoring grant is effective after the approved per-app reset.

The user completed one physical task on the capture-restricted source-policy build. That same unchanged process then refused 27 calibrated native attempts and three adaptive vision attempts using known page geometry. Six native cases were skipped because their controls failed. Window and filtered-display captures returned black images. System screenshot failures and unavailable AX action targets remain inconclusive. Ordinary and direct AX reads recovered no marker, with working matched references.

Fifteen fresh startup controls completed, while fifteen matched candidates showed no software binding or task action. A separate session-insertion matrix recorded eighteen explicit refusals against loaded diagnostics. These are distinct from the physical-session results.

Agent-free operation remains unproven. A permissioned external observer recognized the fake phrase during a new physical task on the unchanged browser binary. Both Unicode and virtual-keycode matchers succeeded. The independent oracle accepted the task, and observer cleanup passed. This establishes a keyboard-observation gap. It does not establish an autonomous website action or arbitrary page disclosure. The current priority is autonomous action prevention while preserving human browsing.

One physical task does not meet the PRD's human compatibility targets. External inspection, unfiltered capture on the current build, and broader session privacy remain open. The offline behavior pilot provides neither a trained classifier nor live adaptive replay evidence.

Recent evidence:

- [Native channel launcher](docs/renderer-channel-launcher-findings.md) passes private descriptor transfer and bounded cleanup controls without administrator access. Cross-user launch and secure enrollment remain open.

- [Private renderer channel](docs/renderer-channel-findings.md) passes three display-pause comparisons and a recovery trial. The separate renderer continues page samples through backpressure and peer exit. Cross-user browser integration remains open.

- [Cross-user page progress](docs/renderer-progress-findings.md) records four denied pause attempts. A fresh page challenge and redraw pass afterward. The browser does not yet use this renderer.

- [Renderer token scans](docs/renderer-token-findings.md) calibrate three reads while preserving untested action status.

- [Renderer AX roots](docs/renderer-root-findings.md) preserve two failed controls and skip candidate queries.

- [Safari remote inspection](docs/safari-remote-findings.md) completes a reference console action and finds no advertised candidate target.

- [Physical-session attacks](docs/source-policy-session-findings.md) preserve the human control and native input results.
- [Adaptive vision](docs/source-policy-vision-findings.md) continues from black images using matched page geometry.
- [Capture routes](docs/source-policy-capture-findings.md) separate filtered-display observations from failed system screenshots.
- [Native semantics](docs/source-policy-semantics-findings.md) record matched tree, focused-element, menu, and action queries.
- [Physical keyboard observation](docs/keyboard-readiness-findings.md) records successful phrase recognition after actual tap readiness.
- [Secure password-entry control](docs/secure-entry-observation-findings.md) separates generated password-field results from the physical ordinary-text leak.
- [Earlier observer controls](docs/keycode-observation-findings.md) preserve inconclusive samples and the timing defect.

- [Keyboard source policy](docs/hid-source-findings.md) records ancestry checks and the narrow hardware profile.
- [Source-policy startup](docs/source-policy-startup-findings.md) records current permissioned startup comparisons.
- [Distinct insertion points](docs/native-insertion-point-findings.md) separates working session controls from inconclusive annotated controls.
- [Local inspector client](docs/local-inspector-policy-findings.md) records a working JavaScript control and the protected-shell comparison.
- [Offline mouse replay](docs/behavior-replay-findings.md) records feature limits without a classifier or live evasion claim.
- [Grant recovery](docs/grant-recovery-findings.md) records the signing checks and approved one-app reset.

Further candidates now compile. Capture pilots ran, but the protected BGRA and NV12 builds failed physical visibility. See [route calibration](docs/route-calibration.md).

- [Foreground controls](docs/foreground-findings.md) show native and semantic bypasses of Secure Event Input and reduced accessibility exposure.
- [Protected HTML pixels](docs/pixel-rendering-findings.md) test the public capture-protection property on a sample-buffer layer.
- [Raw device input](docs/hid-observation-findings.md) separates device observations from application events.
- [Continuous capture](docs/stream-capture-findings.md) records completed-stream frames and matched backdrop controls.
- [Local developer tools](docs/inspector-launch-findings.md) records a confirmed launch override and its process-local startup rule.
- [Drag delivery](docs/drag-delivery-findings.md) records public refusal callbacks, internal keyboard controls, and the inconclusive external preflight.
- [Session recovery](docs/session-recovery-findings.md) records working grants, ten matched external drag-entry trials, and remaining input-calibration limits.
- [Isolated compositor](docs/isolated-compositor-findings.md) compares display crops over a verified owned backdrop.
- [Autonomous research](docs/autonomous-findings.md) records software bootstrap attacks, internal keyboard controls, and scoped read comparisons.
- [Direct menu actions](docs/menu-boundary-findings.md) record a semantic focus bypass and removal of content menus in the revised experiment.
- [Expanded session attacks](docs/device-startup-session-findings.md) record physical startup, input refusals, and screenshot disclosure.
- [Startup navigation](docs/launch-navigation-findings.md) records the launch bypass, bounded fix, and pending physical control.
- [Startup visibility](docs/startup-visibility-diagnosis.md) records the hidden app and repeated-Space regression.
- [Keyboard-only routing](docs/device-keyboard-findings.md) records the first positive physical task and matched input refusals.
- [Accessibility boundary](docs/ax-boundary-findings.md) reduces page exposure but still allows known-layout native input.
- [Physical input](docs/hid-physical-findings.md) records a positive keyboard sample and the missing pointer comparison.
- [Graphics-buffer lookup](docs/surface-findings.md) calibrates isolated fake buffers across processes.

Created in [T3 Code](https://t3.codes).

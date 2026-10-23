<img src="assets/icon.svg" width="64" height="64" alt="">

# agentfreebrowser

A macOS-only research project for an agent-resistant browser, with agent-free browsing as the stronger research goal.

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

The current build is an experimental browser and attack testbed. The default browser does not meet either MVP resistance gate. An earlier keyboard-only experiment recorded one positive physical task and twenty stopped input trials, with four inconclusive trials. A revised build closes the measured automatic launch-URL route. The revised visible control passed a new physical startup task, then refused 27 calibrated native trials and three vision-input trials. Six other native trials remain inconclusive. Its screenshots disclose the page. The project does not meet the agent-free goal. No validated physical trajectory dataset or classifier result exists yet.

Further candidates now compile. Capture pilots ran, but the protected BGRA and NV12 builds failed physical visibility. See [route calibration](docs/route-calibration.md).

- [Foreground controls](docs/foreground-findings.md) show native and semantic bypasses of Secure Event Input and reduced accessibility exposure.
- [Protected HTML pixels](docs/pixel-rendering-findings.md) test the public capture-protection property on a sample-buffer layer.
- [Raw device input](docs/hid-observation-findings.md) separates device observations from application events.
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

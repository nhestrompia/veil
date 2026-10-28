# Remaining agent-free gaps

Status after milestone 152: the frozen preview remains vulnerable to the measured focus action. A separate AgentFreeBrowserEngine target now integrates a WebKit activity policy into the combined browser controller. Six matched diagnostic cases pass, with zero new actions across 18 stable activation cycles and successful resumed typing. Physical validation of the new public app remains pending. See the [engine findings](focus-engine-browser-findings.md) and [publication draft](publication-report.md).

No current physical session exists. The new identity has no effective Input Monitoring grant, and no request has run. The engine depends on this workspace and is not bundled. Hardened Runtime is off. Earlier results on the frozen image cannot establish protection for this new candidate.

The two requirements remain separate. Disclosure prevention stops recovery of a fresh page-only secret. Action prevention stops an external agent from completing a website task, including blind operation. Both require usable human access on the same final build.

Loaded-page trials now cover Google, Wikipedia's search page, and GitHub's search page in the actual preview. The user confirms visible pages before the attempts and unchanged empty search fields afterward. A directed-window key-code route submits the fixed phrase in each readable reference and fails in the preview. The subagent independently repeats the Wikipedia attempt. Scoped window captures are black with readable references. External search and JavaScript URL entry receive explicit browser refusals on GitHub. Four other native routes remain uncalibrated. These bounded results do not establish a general guarantee. See [loaded-page findings](loaded-public-website-findings.md) and the [challenge commands](public-website-challenges.md).

## Protection work that remains

1. Validate the integrated focus defense with physical use on the new image. Obtain this identity's Input Monitoring approval, complete physical text and password tasks, then repeat the external activation attack on that same process. The diagnostic suite covers focus, password focus, blur, visibility, and two frame types. Its generated input does not establish human usability. Forced renderer recovery and other lifecycle or timing routes remain open. The frozen preview's original bypass remains valid.
2. Close the capture gap on the actual preview. Window-scoped streaming returns 948 black complete frames with readable controls before and after. App-filtered display capture delivers no complete candidate frames and remains inconclusive. The unfiltered recorder now passes a fullscreen readable reference across all three filter stages. Actual preview coverage refuses an overlapping window before pixels. No unfiltered candidate sequence runs. Keep the privacy guard intact. First-display, resize, fullscreen, and other transitions remain open.
3. Complete semantic and script access tests. One renderer token comparison recovers the reference marker and no preview marker. Other reads fail their controls. The current scripted inspector client still cannot discover its readable reference. No calibrated external inspector attachment tests this preview. A missing TCP listener cannot establish protection against Cocoa's XPC transport. Playwright requires a compatible automation endpoint. Its Chromium control is separate. Keyboard observation needs a preview-specific result, and Appium Mac2 remains untested.

The evidence is in [stream results](preview-stream-live-findings.md), [compositor calibration](evidence/publication-capture-calibration-results.json), [signed inspector comparison](inspector-bundle-findings.md), [renderer reads](preview-renderer-live-findings.md), [native input](preview-native-input-findings.md), [preview focus bypass](preview-focus-action-findings.md), and [clock actions](clock-channel-findings.md).

## Human use and release acceptance

The frozen preview supports this Mac's measured built-in keyboard and US ASCII. The new engine candidate has no physical-human result yet. Mouse input is disabled. Unicode, input methods, broad website compatibility, and the PRD's human-use targets remain unmet. These are explicit usability limits, not additional agent defenses. A physically black page cannot pass.

Final validation needs one report for the same final image and declared attack suite. It must cover browser transports, accessibility, synthetic and blind input, captures, lifecycle changes, and enabled exports or session residue. Each claimed block needs a working reference. Fresh secrets and task outcomes come from an independent oracle. Required inconclusive results prevent acceptance.

A finite attack suite supports a bounded result about the tested capabilities. It cannot prove protection against all websites and future agents. The project must not call an unfinished test, a permission failure, or a diagnostic-only defense an agent-free MVP.

## Scope that stays fixed

Root attacks, modified browser images, kernel exploits, malicious hardware, and external cameras remain outside the PoC threat model. An agent's separate browser and unrelated API credentials are also outside the browser claim. No new browser feature expansion is needed to finish the protection research.

The cross-user renderer work addresses a measured signal bypass, but it does not supply the preview's visible output and physical input. Do not treat that component's success as integrated protection. The remaining work concerns real enforcement and validation. It is not a missing tab bar or bookmark manager.

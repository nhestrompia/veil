# Agent-resistant browser: proof-of-concept PRD

Status: research specification. The initial shell and independent fixture are implemented. Protection experiments determine the outcome.

Date: October 23, 2026. Platform: macOS only.

## Product decision

Build a minimal macOS browser that lets a person use ordinary websites while preventing external agents from inspecting or operating those websites through the browser. Websites require no changes. The browser accepts arbitrary HTTPS addresses and renders normal HTML, CSS, and JavaScript.

The first deliverable is a focused, 2 to 3 working-day feasibility prototype. Test native input before building meaningful browser UI. Use the results to choose between two outcomes:

- An agent-resistant browser blocks common browser automation and increases the measured difficulty of computer-use attacks. It reports successful attacks and human costs.
- An agent-free browser prevents permissioned external agents from reading or operating its content under the declared threat model. A successful disclosure or action defeats this claim.

The long-term goal remains agent-free browsing. A resistant MVP can remain useful when that stronger goal is unmet. Blocking debugger attachment alone establishes a browser-automation-resistant prototype. It does not establish resistance to computer-use agents.

Use native AppKit with WKWebView for the initial experiment. This is a proposed architecture, not a demonstrated protection mechanism. Keep browser inspection disabled and expose no external automation bridge. Test the remaining macOS routes before building a larger browser interface.

Current research does not establish a supported way to exclude arbitrary browser content from every relevant macOS capture path. Apple calls the old window-sharing exclusion a legacy constant that macOS no longer uses. Electron also documents capture through ScreenCaptureKit despite its content-protection setting. Neither flag can justify the product claim. [Apple window sharing](https://developer.apple.com/documentation/appkit/nswindow/sharingtype-swift.enum), [Electron content protection](https://www.electronjs.org/docs/latest/api/browser-window#winsetcontentprotectionenable-macos-windows).

## Problem and intended users

Local agents can use browser debugging, accessibility trees, screenshots, and synthetic input to read and operate web apps. Antiagent tried to stop these clients within website code. Adaptive screenshot-and-input clients still completed its tasks. Moving control into the browser can remove some access routes, but it does not establish control over the desktop.

The primary user is a Mac owner who wants an agent-free place to browse, research, and use logged-in web apps. The secondary user is a researcher who needs reproducible evidence about which automation routes the browser blocks.

This project does not require app owners to enroll their websites. It does not prevent an agent from opening the same public website in another browser. It does not replace a website's authentication or authorization.

## Evidence that shapes the scope

| Finding | Product implication |
| --- | --- |
| Antiagent blocked fixed-coordinate replay in 30/30 randomized trials, but a drawing observer completed 30/30. | Preserve stable, ordinary web interfaces. Do not depend on layout randomization. |
| Its combined temporal guards stopped the Runtime-enabled control, while bare CDP completed 3/3 sessions. | Deny external automation access before disclosure. Optional framework markers are insufficient. |
| Its current-stack evidence contains one completion and two OCR errors. The saved-results verifier rejects the prevention claim. | A working bypass fails acceptance. Tool errors do not count as protection. |
| Encrypted interface media disappeared from certain captures but remained visible in compositor captures. | DRM is a narrow media result, not protection for arbitrary websites. |
| Apple provides per-view inspection settings, but desktop capture remains a separate mechanism. | Test browser inspection, accessibility, capture, and input independently. |

The [Antiagent review](docs/research/antiagent-review.md) links each local finding to source code and results. The [online report](docs/research/browser-feasibility.md) records primary sources and unresolved platform questions.

## Goals and exclusions

The PoC must answer these questions in this order:

1. With a minimal WKWebView shell, can permissioned native input or accessibility actions operate ordinary web controls?
2. Can the browser deny external debugger access and prevent alternate launch paths from restoring it?
3. Which capture paths reveal content, and can a combined vision-and-input agent complete tasks?
4. Can mouse behavior distinguish people from adaptive attackers at an acceptable rate of false blocks?
5. Which protection results survive normal human use, navigation, and relaunch?

Protected rendering is a separate, conditional research track. It asks whether arbitrary HTML can remain interactive inside an actual capture-protected graphics path. It is not a prerequisite for the initial shell or an assumed solution to native input.

The general-usage target includes public pages and authenticated web apps. Initial compatibility tests cover a representative set, not every website on the internet.

The MVP excludes extensions, account sync, imported browser profiles, a password manager, AI features, a custom rendering engine, and production distribution. Downloads, printing, file upload, media permissions, external app handoff, and third-party sign-in flows remain deferred. Each can add content export or automation routes. The browser must explain unsupported operations.

There is no Windows or Linux build, website SDK, enterprise administration service, server-side browser attestation, or CAPTCHA. Private macOS APIs and changes to system security settings are outside the proposed MVP.

Milestones 58 through 61 found OS lifecycle actions and a native ownership conflict in host-only mitigations. The continued research now includes one isolated WebKit activity-projection experiment. It keeps the original MVP exclusions for production scope. A custom engine, private API, or changed setting is not a passing result by itself. See [the activity boundary design](docs/research/activity-boundary-plan.md).

## Threat model and success contract

An agent is an external program that observes or controls this browser to complete a web task. The browser does not need to identify whether an LLM produced the program's instructions. It must restrict the program's access.

The person controls an intact browser build and the Mac's permission grants. The agent can inspect public source code, adapt its behavior, know the task layout, retry, and run as the same logged-in user. Tests must include agents with Screen Recording and Accessibility permissions already granted. Withheld permissions alone cannot establish agent-free behavior.

Code injection into the browser process, a modified app binary, root access, kernel exploits, malicious hardware, and external cameras are outside this PoC. Same-user launch configuration, exposed integrations, and accessible session files remain relevant attacks. A private profile is not a complete boundary against same-user code.

| Route | Attacker capability | Required outcome or limit |
| --- | --- | --- |
| Browser protocols | Try CDP, WebDriver, WebKit inspection, direct transport access, and relaunch configuration. | No external session can inspect or control protected web content. |
| Native accessibility | Read values and text, inspect descendants, activate controls, and set field values. | Sensitive web content and actions remain unavailable in the strict experiment. Feasibility is unproven. |
| Desktop vision | Use ScreenCaptureKit, screenshot tools, recordings, and sharing. | Test disclosure separately. Known macOS limitations currently prevent a general capture-protection claim. |
| Native input | Use CGEvent posting, keyboard entry, coordinate clicks, scrolling, and accessibility actions. | Agent input cannot complete the task. Event metadata alone is not proof of human origin. |
| Blind input | Use known coordinates or keyboard sequences without reading current pixels. | Hiding content alone is insufficient. Test known layouts and repeated attempts. |
| Exports and integrations | Use clipboard, drag, print, downloads, browser scripting, or external handoff. | No undocumented route exposes protected page content or commands. |
| Session reuse | Inspect browser-created files or reuse credentials exposed by this browser. | No deliberate credential export or content logging. Test accessible residue and document remaining same-user limits. |
| Process signals | Pause and resume a same-user content process without input or code injection. | A page must not complete a protected action from the interruption. Milestone 88 confirms this route in the custom-engine diagnostic. Release signing remains unmeasured. |
| Another browser or direct API | Open a public URL elsewhere or use independently obtained credentials. | Outside the browser claim. This browser cannot revoke those capabilities. |

The current prototype prioritizes independent agent operation. A person completing a task while a listener recognizes a known test phrase is not an agent-input bypass. That sample also does not demonstrate recovery of a fresh page-only secret. Keep keyboard privacy evidence separate from autonomous action and fresh-marker results.

For acceptance, measure disclosure and action prevention separately. Disclosure means recovery of a fresh secret shown only in the current page. Action success means completion of a task, even if the agent cannot read the page. Either result defeats the broad claim that agents cannot use this browser.

An agent-resistant result must name the routes it blocks and measure the routes it only makes harder. Read resistance and action resistance remain separate results. A finite test matrix supplies evidence for those routes, not proof against every future agent.

Accepting a CGEvent proves that particular injection path works. It does not prove that every possible input filter must fail. Conversely, rejecting a few generated trajectories does not establish physical human origin.

## Human experience

The person launches the app, enters an HTTPS address, and uses the site normally. The interface contains an address field, Back, Forward, Reload or Stop, and a protection-status control. One window with one active page is enough for the MVP. Search queries can wait. The address field accepts URLs.

The user can read pages, follow links, scroll, enter text, use keyboard navigation, and sign in through supported first-party forms. Sites keep their normal layout. The browser adds no moving buttons, flicker, hidden decoys, or repeated human challenges.

The status control shows separate capabilities for inspection, accessibility, desktop capture, and external input. It also identifies the tested outcome as automation-resistant, agent-resistant, or agent-free. Runtime configuration and test evidence must remain distinct. A configured restriction does not mean that an external test passed.

For the present macOS design, the status must disclose that desktop capture protection is unproven or unsupported. It must not show a general green "Protected" state. A capability failure must show its limit before the user relies on it. An unexpected failure of an implemented restriction must cover the page and require an explicit recovery action.

Accessibility presents a direct product conflict. Agents and assistive tools can use the same semantic information. The PoC must measure this conflict, including VoiceOver. Do not claim a supported method distinguishes them unless an experiment establishes it. If strict protection removes assistive access, document that restriction and do not call the result suitable for general usage.

## Required capabilities

P0 requirements apply to the relevant acceptance gate. S3 and S5 express the agent-free target and remain research questions for the resistant outcome. Record a negative result instead of removing the failed route. The initial feasibility pass needs only a shell, fixtures, and external attack tools. Full browser controls and export restrictions come later.

| ID | Priority | Requirement | Acceptance evidence |
| --- | --- | --- | --- |
| B1 | P0 | Render arbitrary HTTPS websites with ordinary web JavaScript enabled. Allow loopback HTTP only in the test build. | Documentation, a dynamic app, a long page, and a first-party form work without site modification. |
| B2 | P0 | Supply minimal navigation, visible origin, loading state, and recoverable network errors. Reject script URLs and unsupported schemes. | Manual navigation and redirect tests preserve origin visibility. Invalid certificates cannot be bypassed in the MVP. |
| B3 | P0 | Use an isolated, ephemeral session. Do not import or export cookies or browser profiles. | Login works within the session. Closing the app ends it. Restart and file inspection find no deliberately persisted login store. |
| S1 | P0 | Disable inspectability for every web view. Expose no external evaluation, snapshot, automation, or page-content API. | Attachment attempts fail for the tested release build. A separate exposed control proves the attacker works. |
| S2 | P0 | Prevent alternate entry points from enabling inspection or automation. | Test launch arguments, environment, Apple Events, URL handlers, popups, worker targets, and restored state. Record unsupported vectors explicitly. |
| S3 | P0 research | Restrict external accessibility reads and actions for the web-content subtree. | Fresh secrets, field values, actionable descendants, and hidden text remain unavailable to a permissioned external AX client. |
| S4 | P0 research | Establish desktop capture behavior through independent adapters. | Paired controls, human observations, screenshots, and decoded recording frames establish disclosure or exclusion for each path. |
| S5 | P0 research | Prevent agent-originated native input from operating web content. | Permissioned synthetic mouse, keyboard, scrolling, AX actions, and blind replay cannot complete tasks. Physical inputs still work. |
| R1 | P0 experiment | Collect physical and synthetic mouse behavior, then evaluate adaptive evasion. | Report session false blocks, attacker task success, attack effort, and detection before the action. Use separate people and sessions for evaluation. |
| S6 | P0 | Deny deferred content-export features and host integrations. | Copy, drag, print, download, upload, unsupported permissions, and external handoff fail with clear feedback. URL copying may remain available. |
| S7 | P0 | Apply restrictions before first content display and throughout navigation. | First frame, iframe, redirects, new-window requests, process recovery, and relaunch tests show no weaker content context. |
| U1 | P0 | Preserve stable rendering, ordinary input, text editing, zoom, focus, and keyboard navigation. | Human task measurements meet the targets below. Record IME, dictation, and accessibility incompatibilities. |
| E1 | P0 | Export a local research report without page content, credentials, or session secrets. | Report contains build, environment, route results, errors, timing, and evidence references. Sensitive test evidence remains explicit and separate. |
| E2 | P0 | Use reproducible external tests with positive controls and authoritative task outcomes. | Report block, bypass, or inconclusive per route. A bypass fails a prevention claim for that route and any agent-free claim. |

An ephemeral store reduces routine persistence. It does not guarantee that memory, swap, caches, or every same-user access path contains no data. Those limits belong in the research report.

## Proposed architecture

Use AppKit for the window and browser controls. Use WKWebView for web rendering and navigation. Apple documents `isInspectable` as false by default and controllable per view. Set it explicitly for every view and verify the built app externally. This property covers Safari Web Inspector access, not all desktop observation. [Apple inspection documentation](https://developer.apple.com/documentation/safari-developer-tools/enabling-inspecting-content-in-your-apps).

Use a nonpersistent WKWebsiteDataStore for the first prototype. Apple documents this store as keeping website data in memory. Keep page JavaScript enabled and avoid injected bot-detection scripts. No JavaScript-to-native bridge may expose page reads, arbitrary execution, credentials, or host commands. A debug build with inspection enabled must use a distinct identity and remain separate from the tested build. [Apple website data store](https://developer.apple.com/documentation/webkit/wkwebsitedatastore).

Keep a single owner for content-view creation and navigation policy. New-window requests must stay in the same constrained context or fail visibly. Disable unexpected external schemes and deferred capabilities. Do not load an unrestricted web view to repair compatibility.

Use a sandboxed app with network access and no unnecessary entitlements. Validate a release configuration with Hardened Runtime and no development debugging entitlement. These measures reduce host exposure. They do not establish agent-free operation or solve desktop capture. [Apple App Sandbox](https://developer.apple.com/documentation/security/protecting-user-data-with-app-sandbox), [Apple runtime protections](https://developer.apple.com/videos/play/wwdc2019/703/).

Keep accessibility, native-input, and behavioral experiments replaceable until their behavior is measured. A missing accessibility element flag or input-source field must not silently become a security guarantee. No mouse classifier may replace keyboard or accessibility attack tests. Avoid a Chromium fork, rendering websites into canvas, or encrypted UI streaming in the main MVP.

Electron could simplify a later Chromium compatibility experiment, but it adds host and debugging paths to assess. Its content-protection setting does not solve the documented macOS capture limit. CEF or a Chromium fork adds engine maintenance without supplying evidence that the operating-system routes disappear. The initial WebKit choice minimizes the research build, not the threat model.

Keep the [protected-rendering experiment](docs/research/protected-rendering-experiment.md) separate. Consider Chromium modifications only after identifying a specific graphics path or compositor change to test. Successful OS capture and input injection are not, by themselves, reasons to change browser engines.

## Experiment plan

Use local synthetic fixtures and test accounts. No real financial actions or production secrets are necessary. Include ordinary HTML and dynamic content alongside an adapted Antiagent task.

Start with one WKWebView and a local form. Run T4, T2, and T5 immediately, alongside the basic T1 inspection check. Run T3 next, then combine capture and input. Collect behavior data during these tests, but treat a 3-day classifier result as a pilot.

| Test | Method | Pass condition |
| --- | --- | --- |
| T1: inspection | Attempt attachment, target discovery, DOM reads, script evaluation, and screenshots through available browser transports. Retry after relaunch with hostile configuration. | No target access in the protected build. Attachment succeeds in an exposed control. |
| T4: native input, first experiment | Post pointer and keyboard events. Try scrolling, paste, AX actions, and later combined screenshot/OCR/input. | Agent-free target: no task completes. Resistant result: measure success, difficulty, and remaining bypasses. Physical controls must work. |
| T2: accessibility | A separate permissioned process enumerates the app and web descendants. Read text and values, then try activation and value changes. | No fresh secret or protected action. The control exposes both. |
| T5: blind operation | Give the attacker the exact fixture layout and known workflow. Try coordinate replay and Tab/Enter sequences without capture. | The agent cannot complete actions for an action-prevention claim. Hidden pixels alone cannot pass this test. |
| T3: capture | Capture the app window and display through ScreenCaptureKit, native screenshot tooling, and a recording or sharing app. Check decoded frames. | No fresh secret appears on a claimed protected path while a person can read the page. A missing capture permission is inconclusive. |
| T9: mouse behavior | Compare real mouse and trackpad sessions with basic scripts, replayed human traces, generated paths, and adaptive attacks. | Measure evasion at a fixed rate of false human blocks. Accuracy on basic scripts alone cannot pass. |
| T6: lifecycle | Repeat tests during first display, redirects, SPA navigation, iframe load, popup creation, minimization, fullscreen, and renderer recovery. | No first-frame disclosure or unrestricted content context. |
| T7: session and exports | Check clipboard, drag, print, save, download, logs, caches, crash output, and reuse after quit. | No enabled export or browser-created credential reuse route outside the declared contract. Record unresolved residue. |
| T8: human use | Read documentation, navigate a dynamic app, edit a form, authenticate, and complete the three-decision task. Include keyboard and trackpad use. | Targets below pass with no hidden assistance or moving controls. |

Use a fresh random secret on every disclosure trial. The fixture stores completion outcomes outside the agent-visible browser. Do not export a private in-page state object to decide whether the attacker succeeded.

Run at least 10 fresh sessions for each claimed route and fixture. Give adaptive task attacks up to five minutes and 100 attempted actions per session. These are initial engineering budgets, not security limits. A bypass outside that budget still defeats a prevention claim for that route. Every successful task counts in the resistant results. Pair every route with a working control and keep the exact tool versions.

These repetition targets apply to later acceptance, not mandatory completion of the 3-day pilot. The pilot must identify working attack paths and publish its actual sample sizes. It must not claim a low rate of false human blocks from a few sessions.

The [mouse-behavior experiment](docs/research/mouse-behavior-experiment.md) defines collection, holdout splits, adaptive attacks, and decision criteria. Assess the attacker against the whole browser. Bypassing the mouse classifier through keyboard or AX actions remains a successful attack.

The researcher may adapt the attacker after the first failure. Include one pass that removes optional framework markers and one that combines the strongest available observation and input paths. No rule may require an attacker to enable optional Runtime instrumentation.

Record macOS build, hardware, display setup, scale, permissions, app commit, signing mode, WebKit version information, adapter version, timestamps, and launch configuration. Every unavailable route stays visible as inconclusive. An assertion failure, OCR error, lost window, timeout, or crash never counts as a block.

## Acceptance gates and measures

These thresholds are proposed targets for this project. Antiagent did not measure or approve them.

| Gate | Required evidence | Decision |
| --- | --- | --- |
| G0: valid experiment | Human and attacker controls work. Every result has evidence and environment details. | Repair invalid controls before interpreting a result. |
| G1: browser access | S1, S2, and S7 pass the protocol and lifecycle tests. | A debugger-resistant browser prototype exists. This is partial progress. |
| G2: agent-resistant MVP | G1, core browsing, and human targets pass. Adaptive end-to-end tests demonstrate useful resistance to computer-use attacks at the declared rate of false blocks. | Permit a private research MVP with named limits. Successful attacks remain visible. If only G1 passes, use the narrower automation-resistant label. |
| G3: agent-free behavior | No tested route discloses a fresh secret or completes a protected action. T2 through T7 have no required inconclusive results. Human access also passes. | Any bypass fails the agent-free claim. G3 is not required for G2, and remains a research objective. |

Before a resistant-MVP evaluation, declare the attack suite, budgets, and useful improvement threshold. The initial target is at least a 50% relative reduction in adaptive task completion against the same shell without the defense. Measure at least 30 fresh attempts per condition and report uncertainty. Also report median completion time, actions, and time spent adapting the attacker. A slower attacker with unchanged completion needs a narrower friction claim.

Behavioral acceptance targets no more than 1% false blocks per legitimate session, with uncertainty reported. The small feasibility pilot cannot establish this rate. Compare no classifier, metadata rules alone, behavior alone, and their combination. A mouse-only gain that disappears under keyboard or AX attacks does not establish browser-wide computer-use resistance.

Human targets: three testers complete at least 90% of 15 total core-task sessions. Median task time must stay within 1.5 times the same fixture in Safari. There must be zero unexpected protection lockouts in a 30-minute session per tester. Also test complete keyboard navigation, visible focus, zoom, Unicode input, and VoiceOver. A VoiceOver regression prevents a general-usage claim.

Performance targets on the recorded reference Mac: a usable window within three seconds in four of five cold launches. Added navigation overhead stays below 20% against an unmodified WKWebView shell. Idle overhead stays below five CPU percentage points. These targets require measurement and do not replace protection gates.

Include window activation, deactivation, first-responder changes, visibility, and frame lifecycle as action routes. Measure authoritative outcomes throughout reference preparation, candidate activation, attack calls, and cleanup. An action before the planned input call still counts as a bypass. Milestone 58 confirms a focus-only bypass in three diagnostic processes without posted input. This remains a failed gate until a usable mitigation passes matched controls. See [page findings](docs/page-feature-findings.md).

Published results must name the OS build, app build, tested routes, known bypasses, human-access limits, and sample sizes. Never label an incomplete test matrix "agent-proof."

## Delivery sequence and stop rules

Time budget: one engineer, 2 to 3 working days for a focused feasibility pass. This replaces the initial 10 to 15-day build sequence. It is not a promise of a validated classifier or completed MVP.

1. Day 1: create the minimal WKWebView shell and harmless HTML form. Test inspection, permissioned CGEvent mouse and keyboard input, AX actions, and blind operation. Start physical-input collection.
2. Day 2: test ScreenCaptureKit and system screenshots, then a combined vision-and-input client. Challenge any candidate input restriction and document working bypasses.
3. Day 3, if justified: run a small behavioral pilot against human-trace replay and adaptive generation. Publish the route matrix and choose the next research target.

Do not build tabs, bookmarks, browser polish, or a fork during this pass. The deliverable is a reproducible experiment and a decision about the achievable outcome. A negative result is useful.

If native input and screenshots both work, the existing shell does not support an agent-free claim. That result does not automatically justify Chromium. Continue only with a concrete, bounded hypothesis for useful resistance. If adaptive attacks erase the gain or human costs are unacceptable, keep the research report and stop that defense.

Only after the feasibility decision, scope a private resistant MVP and estimate its work. The larger validation sample, human tests, compatibility checks, and lifecycle tests belong to that follow-up. Agent-free research remains separate if G3 cannot pass.

The protected-rendering track starts only if the evidence identifies a meaningful capture problem and a plausible producer/compositor path. Its time and engine changes are not hidden within the shell budget. A managed OS, remote environment, or different platform would require a new scope decision.

## Main risks and unresolved decisions

| Risk | Present assessment | Resolution |
| --- | --- | --- |
| ScreenCaptureKit reads normal browser content. | Known platform concern. No supported general exclusion established. | Run T3 after the initial native-input tests. Do not build around the obsolete sharing flag. |
| Accessibility hiding fails or removes essential access. | Unproven for arbitrary WKWebView content. | Run T2 and VoiceOver together. Do not equate AX restrictions with selective agent detection. |
| Native input matches physical input closely enough to pass. | No human-attestation mechanism established. | Run T4 and T5, including granted permissions and known layouts. |
| Mouse behavior separates basic scripts but fails under adaptation. | Unmeasured. A high offline accuracy score is insufficient. | Run T9 with human-trace replay, generated paths, held-out people, and keyboard or AX bypasses. |
| A protected-media result does not generalize to HTML. | Antiagent measured a static-media success and a compositor bypass. | Keep the protected-rendering track separate. Require interactive HTML, not a video overlay. |
| Compatibility pressure adds an unrestricted context. | Likely during auth, popups, or file workflows. | Deny unsupported paths visibly. Require tests before enabling each one. |
| Same-user code recovers session material. | Ephemeral storage narrows persistence but is not universal isolation. | Inspect residue and state the tested boundary. |
| OS or WebKit updates change a route. | Results depend on the tested build. | Rerun the route matrix after each supported update. |

Confirmed choices are macOS only, arbitrary websites, local general use, research first, and no website integration. Remaining questions concern technical feasibility, not whether to replace the target with a website SDK or managed kiosk.

The first implementation decision follows the native-input and capture experiments. Decide whether the evidence supports a resistant MVP, further agent-free research, or a documented stop.

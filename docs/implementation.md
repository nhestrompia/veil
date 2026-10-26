# Implementation milestones

## Milestone 1: native research shell

Implemented October 23, 2026, on macOS 26.6, build 25G72, arm64, with Apple Swift 6.4 and the macOS 27 SDK.

The browser contains one WKWebView with inspection disabled and a nonpersistent website data store. It exposes no external page-read, snapshot, or evaluation API. A separate control binary enables inspection at compile time. Both app bundles use Hardened Runtime, an ad hoc signature, App Sandbox, and network-client access. This is a research build, not production distribution.

The loopback fixture owns submission outcomes outside the browser. Controller requests need a random key in a local, ignored file. This prevents accidental validation through browser state. It does not isolate the fixture from unrestricted same-user code. Direct HTTP submissions are oracle tests, not browser-attack evidence.

Two architecture sketches and an independent judge compared direct Swift compilation with SwiftPM. The judge preferred the Python fixture and separate executables. The implementation keeps those boundaries and uses direct compilation for the smallest first build. A Swift HTTP server and a shared browser/attacker library were rejected as unnecessary initial work.

Verification completed:

- Both signed app bundles compile with Swift 6 and warnings treated as errors. Signature verification passes.
- Twelve policy cases cover HTTPS, loopback HTTP, and rejected schemes or hosts.
- The fixture test covers controller authorization, independent trial outcomes, and removal of typed data from event telemetry.
- The protected app loaded the loopback page. Native computer use inspected its window and followed its HTTPS link to example.org.

The native tool exposed the fixture's accessibility content despite disabled inspection. This is an early observation, not a prevention result. Milestone 2 measures reads and actions with an independent oracle.

No human-input baseline, Safari inspector attachment comparison, or capture exclusion result is established by this milestone.

## Run the prototype

```sh
bash scripts/build.sh
bash scripts/test-policy.sh
python3 -m unittest discover -s tools -p 'test_*.py' -v
python3 tools/fixture.py
open -n dist/AgentFreeBrowser.app --args --url https://example.org
```

Use `dist/InspectableControl.app` only as the separate inspection-positive control. The browser accepts HTTPS and loopback HTTP. Clipboard operations remain available for baseline attacks. Full export restrictions are not implemented. The default build has no input defense. The separate filter variant is an experiment with demonstrated bypasses.


## Milestone 2: native attacks

Committed as `548af04`. Added the independent NativeProbe app, permission preflight, CGEvent and AX adapters, paired runner, and strict prevention verifier. See [native-input findings](native-input-findings.md).

## Milestone 3: capture and browser transports

Committed as `6a6eb2b`. Added ScreenCaptureKit and system capture, OCR-driven input, pinned Playwright probes, and separate inspector-discovery evidence. See [capture findings](capture-findings.md).

## Milestone 4: source-state filter

Added `dist/MetadataExperiment.app` and tested the rule against adapted native and vision agents. The generated HID-state events bypassed the filter. See [filter findings](input-filter-findings.md).

The default browser remains an unprotected research baseline. There is no validated behavioral detector or agent-resistant MVP. NativeProbe's user-approved Accessibility and Screen Recording grants remain enabled for repeat experiments. Rebuilt ad hoc binaries need effective-grant checks and may need a fresh registration. Do not grant these permissions to the browser app itself.

## Milestone 5: guarded foreground experiments

Added SecureInputExperiment and ReducedExposureExperiment, with console preflight checks and a cycle-safe AX traversal. Milestone 9 replaces the console veto and completes live attacks. Both policies allow agent actions. See [foreground findings](foreground-findings.md).

## Milestone 6: protected HTML pixels

Added PixelControl and PixelProtectedExperiment with a source WKWebView outside the onscreen window list. The control submitted an HTML snapshot through a sample-buffer renderer. Milestone 8 tests capture routes and physical visibility. Both protected pixel formats fail physical visibility. No input bridge exists. See [pixel findings](pixel-rendering-findings.md).

## Milestone 7: independent device observations

Added a separate HIDObservation app and an unentitled virtual-device probe. Both virtual-device APIs returned nil in three creation attempts. The approved Input Monitoring grant is now effective. Generated-input observations exist. A physical baseline, classifier, and input defense remain absent. See [device findings](hid-observation-findings.md).

## Milestone 8: calibrated routes and pixel formats

Refreshed the approved native grants and replaced the blanket console veto with advisory metadata and matched controls. Added filtered display capture, readiness diagnostics, and NV12 conversion. Matched capture pilots recovered clear control content. The user reported black physical BGRA output while its unprotected control was visible. This rejects that configuration as useful protection. The protected NV12 view also appeared black on the direct display. See [route calibration](route-calibration.md).


## Milestone 9: foreground and semantic bypasses

Added explicit AX window and focus traversal, foreground checks for each generated event, and compositor crops inside research windows. The probe now focuses the fake field before AX value and button actions.

Secure Event Input allowed six native trials, with its mode enabled during all 84 logged input events. The reduced-exposure build allowed all three semantic AX trials and two of three known-layout trials. Its tested captures omitted the marker. These capture observations do not establish input prevention. See [foreground findings](foreground-findings.md) and the saved independent fixture outcomes.


## Milestone 10: isolated graphics-buffer lookup

Added a two-process calibration for direct IOSurface and Core Video allocations. Default and explicit-false allocations returned nil for exact-ID lookup in twelve trials. Six explicit-global controls recovered the exact fake bytes. No browser identifiers, desktop enumeration, or protected-media claim follow from this test. See [surface findings](surface-findings.md).

## Milestone 11: generated-input observations

The observer accepted all fifteen generated-input tasks. Seven trials produced no raw device records. None produced raw keyboard records. Pointer records in other trials remain potentially mixed with physical input. See [generated controls](hid-generated-findings.md).

## Milestone 12: explicit accessibility boundary

Added application, window, and web-view overrides in a separate AXBoundaryExperiment. The tested AX traversal exposed no page marker. The known-layout native agent still completed all three tasks. A computer-use attachment timed out, so that route remains inconclusive. See [accessibility findings](ax-boundary-findings.md).

## Milestone 13: declared physical input

The user supplied a physical session with 97 raw keyboard records. No raw pointer values or accepted fake action appeared. This is a positive keyboard observation, with no complete human-usability result. See [physical-input findings](hid-physical-findings.md).


## Milestone 14: lower-level posting attacks

Added both default and HID-manager options of IOHIDPostEvent to the native probe. All six fake form actions completed. No raw callback appeared in this observer configuration. Apple source still contains a report-producing path. See [posting findings](hid-posting-findings.md).

## Milestone 15: keyboard-only device routing

Added a separate unsandboxed research browser with an approved Input Monitoring grant. The event gate uses exact internal objects through application dispatch. Queue insertion copied the event in the first test, so that design failed.

The user completed one independent website action with the physical keyboard. In the same process, twenty generated-input trials recorded refusal with matched working controls. Four further trials remain inconclusive. No attack added a submission. The build still has an automatic launch-URL route and no pointer support. See [device-keyboard findings](device-keyboard-findings.md).


## Milestone 16: directed keyboard calibration

Added mixed global-click and PID-keyboard routes, with Unicode and physical-key-code variants. Both completed all three controls. The original all-directed route and a window-annotated variant still failed three controls each. The expanded matrix contains 27 completions and six inconclusive results. See [directed-input findings](directed-input-findings.md).


## Milestone 17: physical startup submission

Launch arguments now fill the keyboard browser address without loading it. Three earlier launch trials reached the disposable endpoint. Three revised trials made no requests, with matched controls and effective device access. The latest visible control repeated this zero-of-three result. These are bounded launch results.

Physical startup checks exposed a hidden app and a repeated-Space editing bug. The user confirmed address visibility after explicit app selection. The native field control reproduced address replacement before the dispatcher fix and passed afterward. Repeated binding Spaces now preserve the address until navigation begins. A ready message confirms binding, and normal Space input resumes after navigation.

The shared app path has two mutually exclusive build flavors. The visible flavor enables window sharing for diagnosis. It cannot establish capture prevention. The updated build still requires physical website completion and attacks against that same process. See [startup navigation](launch-navigation-findings.md) and [visibility diagnosis](startup-visibility-diagnosis.md).


## Milestone 18: usable startup and expanded same-session attacks

The user completed physical startup on the revised visible control. The fixture confirmed one accepted action. The unchanged process then refused 27 calibrated native trials and three screenshot/OCR-driven input trials. Six native trials remain inconclusive because their controls failed. No generated trial admitted input or added an accepted action.

Added a runner that captures only the target window and counts new independent actions. The visible control disclosed its page marker in all three captures. This is useful input evidence, with no agent-free claim. See [expanded same-session findings](device-startup-session-findings.md).


## Milestone 19: direct menu actions

A direct File/Edit query exposed commands omitted by the earlier page traversal. The probe selected the browser address through Open Location without an admitted keyboard event. A nil menu getter failed to remove the exported commands.

The keyboard experiment now omits content menus. Physical Command-L uses the exact authorized event path. Live paired reads find no content commands, while the control still exposes Edit commands. Dispatch checks reject ambient and replayed location shortcuts. The clipboard test did not run, and the replacement probe never accesses the clipboard. See [menu findings](menu-boundary-findings.md).


The capture-restricted flavor repeated the menu-absence result and three launch refusals with working controls. Physical usability on this exact binary remains unverified. The user requested autonomous continuation. The native session runner also requires the current probe hash in each matched control before it sends any input.


## Milestone 20: autonomous bootstrap and internal browser controls

Added fresh-process Space/Return bootstrap attacks through five posting routes. All fifteen controls completed their task. No candidate bound a keyboard or admitted input. The results remain observations, with no new physical control.

Added a separate internal diagnostic that verifies startup, Command-L, and a real WebKit form action without a device grant. Direct Accessibility queries recover the readable reference marker, while both diagnostic flavors omit it. Window capture reads the visible flavor and returns black for the restricted flavor. The fixture now retains outcomes without submitted text. See [autonomous findings](autonomous-findings.md).


## Milestone 21: isolated compositor comparison

Replaced the unrestricted compositor adapter with an explicit owned-backdrop route. Ownership, opacity, coverage, ordering, foreground state, and overlay checks run before capture and image persistence. The default vision runner no longer invokes unrestricted display capture.

The readable diagnostic exposed its marker. The restricted diagnostic exposed only the controlled backdrop. Both internal forms completed. An undersized backdrop caused refusal before image creation. No physical visibility claim follows from these diagnostic runs. See [isolated compositor findings](isolated-compositor-findings.md).


## Milestone 22: continuous capture and helper cleanup

Added a completed-frame SCStream adapter with screen output only. Three readable controls disclosed their markers. Three restricted diagnostics exposed only the owned backdrop. All six internal forms completed. The coverage guard applies to every saved image.

The controller now stops a verified timed-out helper before it removes the diagnostic host. Five lifecycle checks cover stale records, process ownership, replacement processes, and shutdown paths. All fifteen Python checks pass. See [stream findings](stream-capture-findings.md).

## Milestone 23: local developer tools at launch

The installed framework enables local developer tools through a launch argument while remote inspectability remains false. Three controls and three attack launches confirm the setting. Three launches with the new startup rule force it off. Every run preserves an unrelated argument.

The rule changes only the process-local argument domain before framework creation. A revised internal browser control still completes its fixture action. No external inspector attachment or new physical control follows from these results. See [local developer tools](inspector-launch-findings.md).

## Milestone 24: separate drag delivery policy

Added a fixed-text drag source and an external controller with research-window ownership checks. The keyboard experiment now refuses public destination callbacks on its web view, window, address field, and dedicated editor. These changes address a separate AppKit delivery path identified in WebKit source.

Two internal controls confirm address editing, navigation, normal submission, and input-triggered submission. The external preflight found ineffective probe grants and sent no input. The native session also reports locked, with unavailable UI windows. No external drag prevention result exists. See [drag delivery](drag-delivery-findings.md).

## Milestone 25: recovered session and external drag entry

Native UI and the approved probe grants work again. Accessibility and computer-use controls complete website actions. Nine CGEvent controls remain inconclusive, including separate source states and insertion points.

An external AppKit source triggers ten reference actions without posted mouse or keyboard events. Ten fresh diagnostic candidates refuse entry and update callbacks, with no new action or page drag event. A separate computer-use pair records the same outcome. The candidate uses a private startup baseline, with no new physical usability claim. See [session recovery](session-recovery-findings.md).

## Milestone 26: retain unchanged probe builds

The probe build now compares source files, build scripts, toolchain versions, and the signed executable. A matching build retains the existing executable. Changed inputs or an invalid signature force a rebuild.

The repeated build retained the exact executable hash and modification time. This avoids unnecessary signing changes during permission diagnosis. It does not replace effective permission checks after a real rebuild. The check is in `artifacts/probe-cache-verification.json`.

## Milestone 27: desktop input recovery and test safeguards

Modifying mouse hooks now prevent input trials before browser launch. Failed input releases no longer depend on foreground ownership. Drag and internal-control controllers wait for exact executable cleanup, including failed readiness. Diagnostic timers limit unattended windows.

All 23 Python checks pass, with a real disposable-process exit check. Swift input-safety, browser-policy, and device-dispatch checks pass. No new desktop attack ran. The user confirmed recovery after DockDoor stopped. The exact interaction remains unexplained. See [desktop input safeguards](desktop-input-safety-findings.md).

## Milestone 28: repeated automation transports and failed-launch cleanup

The isolated Chromium control completes three website actions. Six attachment attempts across three native hosts remain unsupported transports. The failed-launch cleanup stops each new research instance, with no research process left afterward. Executable hashes and cleanup outcomes are saved.

No native input or capture result follows. Native UI is unavailable, the console reports locked, and the rebuilt probe needs its existing grants refreshed. See [automation transport findings](automation-transport-findings.md).

## Milestone 29: restored native calibration and reference gating

The existing probe grants are effective again. Nine of eleven reference routes complete their website task with no modifying mouse hooks. Two mouse routes remain inconclusive. The native controller now skips every candidate whose matched reference fails. All 24 Python checks pass.

The rebuilt browser still needs its separate device grant refreshed. No new candidate result follows yet. See [native calibration findings](native-calibration-findings.md).

## Milestone 30: matched startup trials with effective device access

All fifteen references complete their task. Fifteen matched candidate trials observe no binding, admitted input, or website action. The device reader is ready in every candidate. Cleanup passes for every process. Legacy HID input now releases pending keys after cancellation or lost focus, and all 25 Python checks pass.

This concerns software startup attempts, with no new physical usability or hardware-attestation claim. See [startup confirmation](bootstrap-confirmation-findings.md).

## Milestone 31: scoped capture comparisons and research pause

All three stream references disclose their markers. All three restricted stream captures recover only the owned research backdrop. Three window-image references disclose their markers, while three restricted window images do not. System window screenshots work on all three references and fail on all three restricted diagnostics. Those failures remain inconclusive.

All twelve private bootstrap controls complete one internal form action. Physical visibility on the latest restricted binary remains unverified. The user requested a pause. The fixture stopped, and no research application remained. Resume details are in [the handoff note](HANDOFF.md).

## Milestone 32: external attacks against an already-loaded page

All 33 reference actions succeed. Three unchanged diagnostic processes receive eleven attacks each after private startup. Twenty-seven native attempts are explicitly refused, with no new candidate action. Six Accessibility or vision attempts remain inconclusive. Cleanup passes for all 36 processes, and all 31 Python checks pass.

This is a private diagnostic startup, with no physical binding or human usability claim. See [loaded-page findings](loaded-page-findings.md).

## Milestone 33: working local inspector client

The native UI tool opened the reference inspector and evaluated two console expressions. The first read the expected page path and disclosure marker. The second completed one fixture action, which the independent oracle recorded. Exact process cleanup passed. The reusable controller applies only a volatile launch argument and changes no persistent preference.

This establishes a working local inspector reference. Protected-shell and remote inspector attachment remain separate tests. See [local inspector findings](local-inspector-findings.md).

## Milestone 34: matched local inspector policy comparison

A disposable control with remote inspectability disabled still opens a local inspector under the developer-extras launch argument. Its console reads the correct marker and completes one independent fixture action. Two protected-shell trials with the startup rule offer no Inspect Element entry. A separate ordinary-input control still completes on the readable shell.

One stalled UI attempt remains inconclusive. All four controller cleanups and the extra-process cleanup pass. The probe remains unchanged. This tests one local inspector route, with no device-browser or agent-free claim. See [local inspector policy findings](local-inspector-policy-findings.md).

## Milestone 35: unavailable references stop the input matrix

Eighteen session-insertion references lacked the fixture field. No input adapter ran, no candidate launched, and all reference processes passed cleanup. The console reported locked despite effective probe grants. The results remain inconclusive.

The runner now stops at the first unavailable reference field. A regression check proves that later routes and repetitions do not run. All 32 Python checks pass. The annotated-insertion test remains pending. See [insertion-point findings](insertion-points-findings.md).

## Milestone 36: refuse known software keyboard sources

The router now checks kernel device ancestry before binding. It rejects known software sources and unknown paths. Its first supported profile is the observed built-in FIFO keyboard. A read-only audit classifies one keyboard as eligible and two software paths as refused.

Twelve policy cases, the event-dispatch checks, and all 32 Python checks pass. The full candidate compiles with warnings as errors. The installed app and probe remain unchanged. No new physical or live attack result follows. See [keyboard source findings](hid-source-findings.md).

## Milestone 37: separate session and annotated insertion points

Eighteen session-insertion controls completed the task. Eighteen matched attempts on three loaded diagnostics received explicit refusals, with no new action. Eighteen annotated-insertion references failed to complete and remain inconclusive. No annotated candidate ran.

All 39 processes passed cleanup. The probe remained unchanged. The loaded diagnostics use private startup and do not test the new device-source rule. See [insertion-point results](native-insertion-point-findings.md).

## Milestone 38: offline behavior replay pilot

The offline tool processes one declared physical session and fifteen saved synthetic sessions. It removes source labels and absolute locations from motion features. A copied trajectory preserves every selected feature. Samples without enough motion remain explicitly unavailable.

No classifier trains, no input event posts, and no live replay result follows. The physical task remains unverified. Four new checks pass, and all 36 Python checks pass. See [offline replay findings](behavior-replay-findings.md).

## Milestone 39: recover the rebuilt browser's grant

Off/on and exact-bundle Add did not restore effective Input Monitoring. Read-only signature checks passed, but TCC examined an older code requirement. A user-approved reset of this app's ListenEvent decision, followed by exact-bundle Add, restored access.

The read-only identity helper compiles and refuses unrelated PIDs. Its diagnostic browser passed cleanup. No other permission reset. This restores a test prerequisite, not a prevention result. See [grant recovery findings](grant-recovery-findings.md).

## Milestone 40: startup attacks with the new source policy

Fifteen readable startup controls completed. Fifteen matched fresh candidates had a ready device reader but showed no binding or task action. All thirty processes passed cleanup. Fresh native calibration supplies 27 completed references and six inconclusive PID mouse references.

The physical-session runner now skips failed controls, matches insertion points, checks hooks, and verifies cleanup. Four new checks pass, and all forty Python checks pass. Physical use remains pending. See [source-policy startup findings](source-policy-startup-findings.md).

## Milestone 41: physical use on the source-policy build

The user completed one physical task on the capture-restricted source-policy build. The independent oracle recorded the accepted action, and the process and executable remained unchanged.

Twenty-seven calibrated native attempts then received explicit refusals. No new action or admitted input occurred. Six failed-control cases were skipped. The initial vision adapter failed to create PNG output and remains inconclusive. See [physical-session findings](source-policy-session-findings.md).


## Milestone 42: adaptive vision after physical use

Three window-image references completed. Three matched known-layout attacks continued after black target images and received explicit input refusals. The controller now resolves capture paths, gates candidates on working references, checks the frozen probe, and verifies cleanup. Earlier adapter failures remain inconclusive. See [vision findings](source-policy-vision-findings.md).

## Milestone 43: capture routes in the physical session

Three filtered-display references disclosed markers. Three restricted images were black. Three system screenshots worked on references but failed on the candidate and remain inconclusive. All six references passed cleanup. See [capture findings](source-policy-capture-findings.md).

## Milestone 44: native semantics in the physical session

Three references disclosed markers through ordinary and direct AX queries and completed a task. Candidate reads disclosed no marker or content menu actions. The field/action adapter found no target and remains inconclusive. All reference cleanups passed. See [semantic findings](source-policy-semantics-findings.md).

## Milestone 45: bounded passive keyboard observer

The observer compiles with warnings as errors, rejects unrelated PIDs, and installs no monitor without its own effective grant. Its output saves no raw text or key codes. No physical observation control ran. All 52 Python checks pass. See [observer findings](keyboard-observation-findings.md).

## Milestone 46: stable observer package and evidence index

The separately signed observer app passes signature verification. An actual app launch confirms absent grants and zero collected keys. The app contains no permission-request command. README and the handoff distinguish current physical-session evidence from earlier diagnostics. The browser and NativeProbe remain frozen. The user approved its exact Accessibility addition. A fresh app preflight then confirmed effective Accessibility and listening access. No monitor ran in that check.

The generated readable control then completed its task. The observer received thirteen copies but discarded every copy before reading text because window ownership was unavailable. No phrase matched. Both processes passed cleanup. This is an adapter limitation and supplies no physical disclosure result.

## Milestone 47: PID-scoped passive observation

A listen-only PID tap matched generated fake input in a readable control. The AppKit window-ownership limitation remains separate. See [PID observation](keyboard-pid-observation-findings.md).

## Milestone 48: user-started physical samples

The interactive controller starts observation from a user action. A physical readable reference worked. The first candidate comparison missed the sequence and remains inconclusive. See [interactive observation](interactive-keyboard-observation-findings.md).

## Milestone 49: fixed keycode matcher

A bounded matcher recognizes only the fixed fake sequence. Generated controls matched both decoders. Later physical samples exposed a readiness and timing defect. See [keycode findings](keycode-observation-findings.md).

## Milestone 50: actual readiness and positive physical observation

The enabled PID tap now signals from its running event loop. The first key starts collection after a bounded idle interval. An independent permission check needs no running target. All 66 Python checks and the Swift timing checks pass.

The restricted browser accepted one requested physical task while the external observer matched both decoders from sixteen events. Cleanup passed. This establishes a keyboard-observation gap. The generated reference remains explicitly distinct from a physical reference. See [readiness findings](keyboard-readiness-findings.md).

## Milestone 51: bounded password-entry comparison

The readable ordinary-field control completed one generated task and exposed the phrase through thirteen events. Two password-field trials completed with Secure Event Input active and no observed keys. The listener remained alive after input. The final trial verified acceptance before the liveness check.

Both password listeners ended on later focus loss. No physical password claim follows. Every process passed cleanup, and Secure Event Input was off afterward. The restricted browser stayed unchanged. All 66 Python checks pass. See [secure-entry findings](secure-entry-observation-findings.md).

## Milestone 52: Safari remote-inspector control

Safari attached to the inspectable reference without local developer extras. Its Console read the fresh marker and completed one independent task. The Mac target menu omitted the unchanged candidate. This is discovery evidence, not a direct connection refusal.

The approved temporary Safari setting returned to off. Reference cleanup passed. The PRD now separates recognition of physical typing from autonomous input. See [remote findings](safari-remote-findings.md).

## Milestone 53: scoped renderer root calibration

A separately approved AX helper discovers only research-owned WebContent processes. It verifies exact paths and process start times. Its fixed action adapter requires the disposable loopback fixture.

Both direct-renderer reference attempts failed. Host initialization exposed an application role but no controls or page marker. Both candidate queries were skipped. All cleanup checks passed. All 70 Python checks and the Swift ownership and URL checks pass. See [renderer findings](renderer-root-findings.md).

## Milestone 54: bounded renderer tokens

The helper constructs process-scoped remote tokens with explicit scan and traversal budgets. Three readable references recovered their fresh markers. Three matched candidate reads recovered no marker or fixture control within IDs 0 through 1,023.

Candidate writes were skipped because reference actions failed the fixture URL guard. Read and action controls are now independent. The approved app-only permission refresh restored access. All 70 Python checks and Swift boundary checks pass. See [token findings](renderer-token-findings.md).

## Milestone 55: native host Reload comparison

Three fresh references completed external AX Reload actions, each with one new fixture page-ready event and no form action. Three matched candidate scans resolved neither the address field nor Reload button. No candidate action ran. This is a bounded discovery result, not proof that all direct actions fail.

The approved exact-bundle re-add restored effective Accessibility after user authentication. All 74 Python checks and Swift ownership checks pass. All temporary processes passed cleanup. See [host navigation findings](host-navigation-findings.md).

## Milestone 56: actions in the current physical session

The unchanged PID 61893 received 29 calibrated native blocks and admitted no input. Twenty-two cases remain inconclusive across the complete matrix and its follow-up. The fixture recorded no new website action. Three semantic references completed their actions; candidate targets remained unavailable, so no candidate semantic action ran.

The new controller pairs fresh references with this physical session. It checks foreground activation before geometry, preserves failed controls, and stops on accepted input or missing candidate geometry. An interrupted geometry setup remains separate evidence. All temporary processes passed cleanup. All 80 Python checks pass. See [current session findings](current-session-attack-findings.md).

## Milestone 57: engine and content-export policy

The protected configuration disables sharing, asynchronous clipboard access, WebAuthn, Apple Pay, Writing Tools, and element fullscreen. Exact private feature keys and effective readbacks are required before page loading. Three readable views exposed the first three interfaces; three protected views did not. An unknown required key correctly refused startup.

A restricted web view refuses native export responders and Services. Response checks and download cancellation cover response-side export paths. Native selection export remains inconclusive because its readable marker control failed. The new policy completed one private authorized keyboard task. The physical PID 61893 remains unchanged. All 82 Python checks, Swift policy checks, and device dispatch checks pass. See [content policy findings](content-policy-findings.md).


## Milestone 58: cross-page tests and focus-only bypass

Seven private page baselines passed. Their 35 external cases produced 21 native blocks and 14 inconclusive results. A fresh textarea retry passed unchanged. Srcdoc remains unusable under the current navigation policy.

Three activation-only comparisons each completed a new candidate action. The helper posted no input and made no Accessibility call during the activation cycle. This defeats the prototype's broader all-pages action claim. The controller now counts actions during foreground preparation, including failed reference setup. All 85 Python checks pass. Temporary processes passed cleanup. See [page findings](page-feature-findings.md) and [focus research](research/focus-boundary.md).


## Milestone 59: focus hypotheses and visibility actions

Separate activation-filter and logical-key diagnostics stopped their matched focus actions and preserved private typing after return. Both still completed visibility-triggered actions. Three final activation-filter candidates each recorded two new actions during hide and restore, with zero admitted input. The password control failed to switch away, so its candidate comparison was skipped.

No failed hypothesis is enabled in production. All temporary processes passed cleanup, and Secure Event Input was off afterward. All 87 Python checks pass. See [lifecycle findings](lifecycle-findings.md).


## Milestone 60: embedded documents and the complete editor matrix

Navigation and response policies now accept exact about:blank and about:srcdoc documents only inside frames. Top-level addresses and other schemes remain restricted. The srcdoc task passed and refused its matched HID attempt.

All nine private editor/frame baselines passed. Their 45 external cases produced 27 native blocks and 18 inconclusive results, with no new task through those routes. Every temporary process passed cleanup. All 87 Python checks, Swift policy checks, device-dispatch checks, and both production type checks pass. The focus and visibility bypasses remain open. See [embedded-document findings](embedded-document-findings.md).


## Milestone 61: stable activity and native ownership failure

A diagnostic holds logical key, visibility, and occlusion state steady while preserving actual key-window and foreground-PID routing checks. One comparison per mode stopped visibility, blur, and password focus actions. All three resumed private tasks completed.

The password candidate retained Secure Event Input while hidden. Its readable control released ownership. Every temporary process passed cleanup and left Secure Event Input off. This failed condition blocks production use of the host getter approach. Pinned source research defines the next boundary between DOM activity and actual native ownership. See [stable-activity findings](stable-activity-findings.md).


## Milestone 62: separate page activity from actual input eligibility

Three independent sketches and a separate judge selected an outgoing-only WebKit activity projection. It preserves raw UI-process state, sets all five protected content flags, and seeds new content processes. The configuration is immutable for a view. There is no activity-commit API or delayed native replay.

The design retains actual key-window and foreground checks for input. Native ownership and current password state require a separate verified barrier. Aggregate Secure Event Input supports owner attribution only as a source-backed inference. The earlier hide receipt did not establish another foreground app.

A cross-provider review failed before execution because its configured key expired. An available native reviewer completed the comparison, with reduced model-family diversity. The full engine is neither downloaded nor built. Read-only toolchain and resource checks passed. The next unit is the isolated projection patch. See [the design](research/activity-boundary-plan.md).


## Milestone 63: pinned engine patch and compiled projection

A generated six-file WebKit patch adds an immutable per-view policy and projects activity at the two bounded outgoing sites. It leaves native activity calculation and secure ownership code unchanged. Twelve source hashes and exact zero-fuzz patch application pass.

The actual projection header compiles with the pinned enum declaration. Exhaustive checks pass for 65,536 flag sets in both modes. Native identity, five protected flags, other flags, and idempotence pass. This does not compile or validate WebKit integration. All 89 Python checks pass. The full engine remains unbuilt and runtime attacks remain pending. See [engine reproduction](../engine/README.md) and [evidence](evidence/engine-projection-results.json).


## Milestone 64: full source preparation and audit

The pinned source dependency passed all twelve hashes and pristine reuse. The isolated shallow sparse clone retained about 1.8 GB. Preparation enforces storage limits, a 60 GiB free-space reserve, and cleanup of its own process group. All 92 Python checks pass.

The full-source audit covers the discovered activity sender and shared creation path, including recovery and remote pages. Initial empty documents and independent initial-focus operations limit broader claims. The source remains unpatched, unbuilt, and unexecuted. See [the audit](research/activity-full-source-audit.md) and [evidence](evidence/engine-source-results.json).


## Milestone 65: direct native ownership evidence

A read-only diagnostic checks WebKit ownership through its private testing getter. One matched ordinary password comparison released ownership while hidden. One stable-host comparison retained ownership while another research app became foreground. Both resumed one private task. The ordinary focus-only bypass reproduced. Cleanup passed and Secure Input returned to off. The default diagnostic was restored. See [ownership findings](secure-owner-findings.md).


## Milestone 66: exact source staging and bounded build

The build helper checks all old or new source states before writing. It refuses unknown changes and can resume partial application. All 95 Python checks pass. The exact six-file patch is applied to the pinned dependency.

The first build stopped before compilation because root configurations were absent. The corrected source list includes them. The corrected scheme includes engine dependencies. A second attempt started compilation with four jobs, reduced priority, workspace outputs, a two-hour limit, and a 60 GiB disk reserve. The engine remains incomplete and runtime results remain pending. See [build instructions](../engine/README.md).


## Milestone 67: engine identity refusal and Metal compiler

The diagnostic requires the private activity API and expected UI images. Its controller requires the own content executable and all three mapped framework paths. A real system fallback refused before creating a window. All 99 Python checks and the diagnostic compile pass. Positive custom-engine identity remains unverified.

The second build stopped because the actual Metal compiler was absent. Apple MetalToolchain 27A266a now executes. The third attempt runs with quiet logs and a macOS 26 deployment target. Full engine compilation and live engine attacks remain incomplete. See [runtime findings](engine-runtime-findings.md).


## Milestone 68: child-frame lifecycle controls

The fixture now arms lifecycle listeners inside same-origin, cross-origin, and srcdoc frames. One fresh matched comparison per type reproduced one focus-only action with zero admitted keyboard events. All private baselines, resumed tasks, and cleanup checks passed. All 99 Python checks pass. The feature matrix also accepts the strict engine identity path. No custom-engine comparison ran. See [child-frame findings](child-frame-findings.md).


## Milestone 69: preserve sandboxing during generated-source builds

The actual Xcode sandbox profile reproduced the shared temporary-directory refusal. A target-local directory passed. The build now gives each target its own TMPDIR. The narrow WTF target changed from failure to success and generated all four Mach exception files. Engine source and script sandboxing remain unchanged. The full build restarted. See [temporary-directory findings](engine-temp-findings.md).


## Milestone 70: compare cached and uncached Swift compilation

The fourth full build reported Swift task failures despite zero exit codes. A narrow JavaScriptCore build passed with compilation caching disabled. The installed Xcode specification identifies a Swift-specific switch. The fifth full build now disables only Swift caching. Full WebKit compilation and live custom-engine tests remain pending. See [cache findings](engine-cache-findings.md).


## Milestone 71: child-frame visibility controls

Three fresh matched comparisons reproduced two visibility-triggered actions each inside child documents. The frame types were same-origin, cross-origin, and srcdoc. Every private baseline, resumed task, and cleanup passed. The helper posted no input during the cycles. The custom engine remains untested. See [child visibility findings](child-visibility-findings.md).


## Milestone 72: retry the broader cache setting

The Swift-only cache experiment still failed WebGPU and PAL tasks. The sixth full build uses the exact umbrella cache setting from the passing narrow comparison. The diagnostic now reads its own content executable through proc_pidpath. It compiles. All 100 Python checks pass, including rejection of changed line endings before source mutation. Positive custom-engine identity and live engine results remain unverified. See [retry findings](engine-build-retry-findings.md).


## Milestone 73: observe content focus and visibility

The optional page observer records state transitions and page-local timestamps. A matched ordinary password comparison calibrated hidden and visible focus transitions. Its focus-only action reproduced. Private resume and cleanup passed. All 100 Python checks pass. Custom-engine native and stable comparisons remain pending. See [activity findings](page-activity-findings.md).


## Milestone 74: correct quiet-log interpretation

A forced PAL compile emitted the quiet-mode error wrapper but exited zero and regenerated its object. The previous full-build cache interpretation was unsupported. Those runs stopped before their final exit status. The full build now uses normal logging and upstream caching. Explicit future receipt states distinguish success, failure, and a stopped monitor. All 102 Python checks pass, including two real child-process status checks. See [log findings](engine-log-findings.md).


## Milestone 75: graceful-quit controls and strict helper scope

Readable pagehide and unload references terminated without recording beacon actions. The candidate comparisons were skipped. A third reference checked the refactored helper. All cleanups passed. Pure scope checks cover the two exact disposable targets and reject physical or mismatched identities. The rejected optional physical refusal check did not execute. All 102 Python checks pass. See [quit findings](quit-lifecycle-findings.md).


## Milestone 76: build for the host and preserve source timestamps

The seventh build failed on APIs requiring macOS 26.2 because the deployment target was 26.0. The eighth uses the host version, 26.6. Source staging now skips byte-identical files. Its timestamp regression changed from failure to success. All 102 Python checks pass. The complete engine and runtime comparisons remain pending. See [host findings](engine-host-findings.md).


## Milestone 77: separate private typing from activation results

The controller now marks an activation cycle inconclusive when the input gate admits any key during that cycle. Its own scheduled typing can no longer establish an autonomous action or a block. Zero-input accepted actions retain their bypass result, even when activation receipts fail.

Custom-engine diagnostics delay the private resume sequence for twenty seconds. This leaves time for the fifteen-second framework mapping check before external activation. The controller allows twenty-four seconds for that resume sequence. Ordinary diagnostics retain their existing timing.

All 105 Python checks pass. Both ordinary and stable-engine diagnostic variants compile. A fresh ordinary password comparison reproduced one focus-only action with zero admitted keys. Private resume and all cleanup checks passed. Secure Event Input returned to off. The full engine build remains active. Custom-engine identity and action comparisons remain pending.


## Milestone 78: isolate the engine scheme from ImageDiff

The eighth command completed the WebKit scheme in 2,088.594 seconds. It then exited 64 while starting ImageDiff. That separate project cannot accept the inherited derived-data option without a scheme.

The controller now invokes the same WebKit scheme directly through xcodebuild. Its arguments retain the workspace paths, target, four jobs, and reduced priority. ImageDiff is outside this browser experiment. The retry preserves completed objects and uses the same source patch. The overall failure receipt remains saved separately.

The direct retry exited zero in 19.1 seconds. All 105 Python checks pass. Runtime framework identities and action comparisons remain unverified.


## Milestone 79: validate content framework paths

The first identity check refused before any candidate activation. The parser treated the slash in vmmap permissions as a path prefix. A fresh diagnostic reproduced the exact error. A regression check failed before the parser correction.

A second refusal came from rows that vmmap labels unused. Those rows describe shared-cache fragments on dirty pages. The saved rows show all three custom frameworks with executable text mappings. System framework fragments carry the explicit unused label.

The parser now ignores only rows with that unused prefix. Such rows cannot satisfy the required identities. Actual system framework mappings still cause refusal. The controller saves only framework mapping rows for diagnosis. Both new unused-row checks failed before this correction.

The diagnostic and frozen probes retain their existing identities. No candidate activation result follows from the failed identity trials.

All 108 Python checks pass. A fresh native-mode trial verified custom framework paths in both processes. It reproduced one focus-only action with zero admitted keys. Private resume completed one task. Ownership released while hidden and returned afterward. Every temporary process passed cleanup, and Secure Event Input returned to off.


## Milestone 80: stable content activity with native password ownership

Three fresh stable-engine password trials recorded no new focus-triggered action. Each matched readable reference completed one focus action. The native-mode custom engine also reproduced that action before these trials.

Each stable trial admitted zero keys during external activation. The page continued to report visible and focused state while hidden. Actual AppKit key and visibility states became false. Another research app became foreground in the settled sample.

The per-view Secure Event Input flag became false while hidden and true after return. Every private resumed sequence completed one task. All temporary processes passed cleanup. Aggregate Secure Event Input returned to off.

These results apply to the measured focus route. The patch remains isolated from the physical browser. Blur, visibility, child frames, changing password fields, and physical usability still require separate controls. This result does not establish agent-free operation across the web.


## Milestone 81: compare native and stable activity across frame types

The new controller builds each mode of the same isolated engine diagnostic. It runs a native control before accepting a stable result for each case. Failed controls cause explicit skips. Each case uses a fresh process, verified content framework mappings, and a private resumed typing control.

The cases cover password focus, ordinary blur, ordinary visibility, and focus plus visibility in three child-frame types. Those types are same-origin, cross-origin, and srcdoc. The controller stops if stable mode permits an autonomous website action. It preserves per-case receipts and verifies process cleanup.

These comparisons exercise page code that reacts to native activity. They do not prove physical usability, pointer support, or compatibility with every website. Timing behavior and independent element-focus commands remain separate tests.

The first complete matrix reproduced all nine native actions. Seven stable cases recorded no action and passed private resume. Both srcdoc cases recorded no action, but their resumed typing controls failed. All eighteen cases passed process cleanup. These two cases remain inconclusive in the original receipt.

A fresh srcdoc focus retry recorded no action and passed its resumed task. The first retry could not reach the stopped fixture and launched no app. The later retry used the restored fixture. All 111 Python checks pass, including missing-control skips and preservation of positive action evidence after a failed resume.

The fresh srcdoc visibility retry also recorded no action and passed one resumed task. Both retries passed cleanup and left Secure Event Input off. Their successful results do not erase the two original inconclusive cases. The resume failures remain unexplained.


## Milestone 82: timer-gap calibration

The new local fixture arms one timer action after the private startup task. A gap above 500 milliseconds triggers that action once. The controller requires exactly one startup action, then a three-second stationary period without another action. Only then does it hide and restore the app for three seconds. It posts no external input.

The first native-engine run already contained two accepted actions before the stationary period. A timer gap of 516 milliseconds occurred before the attack. Its later hide cycle recorded no action. That sequence cannot calibrate a timing attack. The controller now rejects an early action instead of accepting that sequence as a valid stationary control.

No stable comparison follows without a valid native control. This experiment does not show that timing behavior is protected. All 111 Python checks pass. The physical browser and permissioned probes remain unchanged.

The fresh guarded run also contained two initial actions. It returned inconclusive before hiding the app. Both temporary processes passed cleanup, and Secure Event Input returned to off.


## Milestone 83: active-page timer bypass

A small animation keeps the foreground fixture active. This distinguishes the experiment from the static page that triggered before the attack. Both native and stable modes began with exactly one startup action. Both passed three stationary seconds without a new action or admitted key.

Hiding each app for three seconds triggered one accepted website action. Native mode recorded a timer gap of 1,001 milliseconds. Stable mode recorded 830 milliseconds. Both activation cycles admitted zero input events. No external input or candidate Accessibility action was sent.

The stable page continued to report visible and focused state. The retained visual-idle flag controls timer alignment independently in the pinned source. This identifies the next hypothesis for a bounded patch. It does not yet prove that changing that flag closes the route.

Every temporary process passed cleanup, and Secure Event Input returned to off. The evidence includes engine receipts and framework hashes. Agent-free operation remains unmet.


## Milestone 84: clear serialized visual-idle state

The research projection now clears IsVisuallyIdle in stable mode. It still sets the five focus, visibility, and window flags. Native mode remains an identity operation. The native UI state and Secure Event Input source remain unchanged.

The exhaustive projection check first failed on the new visual-idle invariant. It now passes all 65,536 states in both modes. Every other flag retains its input value. All 112 Python checks pass.

Source staging accepts only the exact measured predecessor header by its SHA256. A changed predecessor is refused before any other file write. Existing timestamps remain intact for byte-identical source. The prior engine receipt, source receipt, and log remain saved separately.

The isolated engine rebuild completed with exit zero in 50.3 seconds. The first native timer control triggered before hiding and returned inconclusive. The stable comparison did not run. The new source rule is not yet a verified runtime fix.


## Milestone 85: adaptive timer controls and desktop prerequisite

The first readiness check required ten intervals below 200 milliseconds. Its native control never reached that condition. The controller skipped the stable comparison and cleaned up both research processes.

The adaptive variant measures ten baseline intervals. Its action threshold is the greater of 500 milliseconds or the observed maximum plus 250 milliseconds. The page records its threshold before the stationary control. The controller then requires three unchanged seconds and performs an eight-second hide cycle.

The native trial measured a maximum interval of 1,000 milliseconds and chose a 1,250-millisecond threshold. Its stationary control passed. No timer action followed. Hide succeeded, but return activation failed. The result is inconclusive, and stable mode was skipped.

macOS also reported the console locked. That flag remains advisory. The failed activation receipt independently prevents a valid negative comparison. All 112 Python checks pass. Temporary process cleanup passed, and Secure Event Input returned to off. The revised engine remains compiled, with its runtime repair unverified.

A desktop-unlock request is pending. Resume with the adaptive timer comparison after foreground controls work. Then run the password ownership control and the broader editor/input matrix. Keep the frozen physical browser and permissioned probes unchanged.


## Milestone 86: unlocked timer comparison

Three fresh native/stable comparisons passed their stationary controls. Each native mode completed one timer-triggered action after hiding. Native gaps measured 1,000, 1,000, and 1,079 milliseconds. Each stable mode recorded no timer action during the same eight-second hide cycle.

All six activation cycles admitted zero input events. UI and content framework identities passed in every trial. Every temporary process passed cleanup. Secure Event Input returned to off after every comparison. The frozen physical browser and probes remain unchanged.

These results support the revised projection for the measured adaptive timer route. They do not establish every timing signal or website as agent-free. Native ownership, independent element focus, and additional external actions remain separate checks.


## Milestone 87: revised-engine editor and password checks

All nine private editor baselines passed on the revised engine. The matched matrix blocked 27 native attempts across ordinary forms, textareas, editable content, both shadow modes, SPA content, and three frame types. Eighteen vision and Accessibility cases remain inconclusive. No accepted agent input or new website action appeared. Every temporary process passed cleanup.

The separate password comparison admitted zero keys during activation and recorded no focus-triggered action. The per-view protection flag released while hidden and returned before private resumed typing. That sequence completed one task. Cleanup left Secure Event Input off.

All 112 Python checks pass. These generated baselines do not replace physical-human controls. Pointer support, dynamic password changes, and independent process or website-action routes remain unverified. The physical browser and permissioned probes retain their frozen binaries.


## Milestone 88: external process signals

The new helper pauses only a verified custom-engine content process owned by a disposable diagnostic session. It checks exact paths and process start times. An independent watchdog resumes the same renderer even if the helper dies. Six pure scope checks exclude the physical browser, system WebKit, and invalid targets.

Two normal comparisons and one watchdog-recovery comparison each produced a website action in native mode and stable mode. All six stationary controls passed. No cycle admitted keyboard events. Every renderer resumed and every disposable app passed cleanup. Secure Event Input returned to off. All 116 Python checks pass.

The current engine remains vulnerable to this timing route. Both measured executables lack Hardened Runtime. A disposable signed control is the next test. Endpoint Security offers a possible authorization boundary but requires separate prerequisites and approval before installation. See the process-pause findings and signal-boundary research.


## Milestone 89: Hardened Runtime signal control

Ordinary and Hardened Runtime command-line targets both accepted external SIGSTOP and SIGCONT. Signature verification, runtime-flag readback, exact child-path checks, and stopped-state observations passed. Each signing mode also passed a separate watchdog-recovery trial. All four targets and watchdogs exited successfully.

This control rules out an ordinary Hardened Runtime signing change as the signal-denial boundary. It does not test a fully hardened browser or establish a sandbox-specific result. The current custom engine remains vulnerable to the six website actions from milestone 88. A privileged enforcement design needs separate prerequisites and approval before installation. No service or permission changed.

A fresh repeat reproduced all four outcomes. Across both runs, four Hardened Runtime trials and four ordinary-signing trials observed the external pause. Every target and watchdog passed cleanup. The final controller also refuses to rebuild a control while that exact executable is running.


## Milestone 90: scoped signal authorization

The new prototype limits SIGSTOP denial to one exact disposable target for at most fifteen seconds. It matches the PID, path, and process start time. It leaves other signals, unrelated targets, stale identities, and expired windows allowed. Pure checks cover these boundaries and exclude the frozen browser and system WebKit.

The compiled helper reports no entitlement and no root privilege. The user confirmed no Apple-granted entitlement for this project. Six integration checks verify target parsing and safe refusals without creating an ES client or subscription. All temporary controls exited. All 116 Python checks pass.

The adapter is compiled, not validated as an enforcement boundary. Live testing needs approved signing, privileged deployment, explicit approval, and independent coverage controls. No service or permission changed. The pause bypass remains open. Continue browser tests that use existing permissions.


## Milestone 91: focused password transitions

Four fresh diagnostics each complete one startup task and four field-type transition tasks. The 300-millisecond controls match the requested type throughout typing. With no added wait, the first password key sees protection off and the first text key sees it still on. Both native and stable engine modes show the same pattern in two comparisons.

Own-view and aggregate snapshots agree. They do not establish key recovery or agent-generated input. All engine identities and temporary cleanup checks pass. Secure Event Input returns to off. All 123 Python checks pass. The next experiment adds a separate foreground owner with balanced release and a readable-app control. No production browser change is enabled.


## Milestone 92: bounded private-entry owner

The diagnostic now supports explicit private-entry sessions with a ten-second policy limit. Its separate owner balances native protection calls and refuses input without current ownership and actual native focus. Focus loss ends the session. Timer expiry and explicit completion release its ownership. The timer needs a running process and does not solve hostile process suspension.

Two stable-engine runs keep aggregate protection on before all transition and resumed keys. Each completes six private tasks and one readable reference task after native release. The final run also observes protection off after timer expiry. Nine acquisitions match nine successful releases. Every temporary process passes cleanup.

All 56 pure private-entry checks and 124 Python checks pass. This remains a diagnostic feature without physical-human, observer-resistance, or general-website proof. The ordinary diagnostic is restored without delayed private input. No production browser feature or permission changed. The next external signal-denial experiment still needs an Apple-granted entitlement and approved deployment.


## Milestone 93: guarded external input matrix

The external-only diagnostic schedules no private typing after startup. Its ten-second protection window has a native timestamp marker. The controller requires active protection at both ends of an attempt, stable elapsed clocks, a deadline margin, and no private-input overlap. Failed references and posting errors cannot establish a block.

All 27 readable controls and private baselines complete. Three external routes across nine surfaces produce zero admitted events and no new candidate task. Every lease expires cleanly, every temporary process passes cleanup, and all UI/content engine identities pass. All 130 Python checks pass.

This is a regression result for the existing input gate with the new session owner. It does not isolate the owner's effect or establish physical-human, general-site, capture, or inspection resistance. The ordinary diagnostic is restored without delayed typing. A separate geometry helper compiles but has no effective posting access. It requests no grant and posts no input. Continue geometry research through the already-authorized computer-use tool if available.


## Milestone 94: native window geometry controls

The fixture now records move and resize actions after one accepted startup task. A bounded controller compares readable and stable-engine diagnostics. It requires a stationary baseline and a successful reference before a candidate attack. Missing input, failed controls, and late receipts remain inconclusive.

Computer-use zoom resizes the readable control and produces one new task without keyboard input. The candidate times out before an action attempt. Both native mouse controls refuse point coverage. A read-only check identifies a Dock-owned layer-20 window above the target at both initial points. The helper retains its safety check.

The user approves the separate helper's Accessibility request. Its packaged preflight confirms effective posting access and no modifying hooks. The executable remains unchanged after the grant. All 135 Python checks and pure Swift path checks pass. Temporary apps exit and aggregate protection returns to off. Frozen browser/probe hashes match. No Endpoint Security client or privileged service starts.

See [geometry findings](window-geometry-findings.md). Agent-free operation remains unmet. Continue with safe geometry calibration and the unresolved process-pause boundary. The latter still lacks an Apple-granted Endpoint Security entitlement for its proposed live denial experiment.


## Milestone 95: diagnostic frame policy and feasibility review

A separate readable shell can pin its native frame. Actual AppKit tests confirm ordinary move/resize behavior, then preserve the pinned frame through eight operations. The policy removes movement and resizing for humans too. It remains outside the production browser.

The external pilot completes its ordinary startup task but receives no timely geometry action. Computer use returns after cleanup and reopens an empty shell. The controller preserves the inconclusive result and skips the fixed comparison. The extra empty shell is closed after executable verification.

All 139 Python checks and AppKit controls pass. Temporary processes exit and Secure Event Input is off. Frozen app and probe hashes match. A primary-source review finds no demonstrated ordinary-app signal-denial boundary here. Identity isolation is untested. Clock changes need independent timing controls. No permission or operating-system service changes.


## Milestone 96: independent timing channels

The disposable fixture now measures main-page performance time, wall time, worker time, and independent server time. A temporary loopback server returns uncached timestamps without task-state changes. The controller owns its lifecycle and saves failed trial errors before cleanup.

Sixteen repeated trials produce sixteen actions across four clocks and two engine modes. All stationary controls pass. Every scoped pause, normal resume, and watchdog recovery verifies. No cycle admits input. All framework identities and temporary cleanup checks pass. The separate two-trial server pilot also succeeds. The hide/restore regression still produces a native action and no stable action.

The existing prevention verifier rejects the eight stable cases despite their successful native controls. All 141 Python checks and JavaScript syntax checks pass. These results expose timing channels. They do not validate a clock patch or a general signal-denial guarantee. No grant, service, input hook, frozen browser, or frozen probe changes.


## Milestone 97: finite identity-boundary experiment

A new native diagnostic prepares permanent credential drops for freshly forked children. It accepts no target PID, user ID, path, or arbitrary command. Root mode requires protected temporary staging. No privileged test ran.

Seven unprivileged controls pass. These include normal stop/resume, inherited signal-state normalization, watchdog-only recovery, process-group interruption, and parent death. Four invalid or unprivileged root invocations refuse. All temporary children exit. All 145 Python checks pass.

A primary-source review corrected staging, signal inheritance, watchdog isolation, and cleanup ownership before the administrator request. The exact binary and command hashes bind the reviewed plan. The next test needs explicit approval for a temporary root parent. It creates no account, service, browser grant, or input hook. A successful command-line comparison would still leave browser integration untested. See [identity findings](identity-signal-findings.md).


## Milestone 98: measured cross-user signal denial

Milestone 98 completed the one approved administrator experiment. The exact reviewed binary and command hashes match the saved plan. The launcher exited with code zero.

The same-user actor and target used user ID 501. SIGSTOP succeeded, the parent observed the stopped child, and an explicit resume restored its heartbeat.

The cross-user target used the existing nobody identity, user ID 4294967294. The actor used user ID 501. Kernel records confirmed real, effective, and saved credentials after permanent drops. Its SIGSTOP returned EPERM. The target never entered a stopped state and answered after 0.111 seconds. That answer preceded any parent recovery signal and the watchdog's two-second recovery limit.

All children exited. The helper removed its protected temporary directory. An independent check found no staged executable process or remaining directory. Later commands ran as user ID 501. Frozen browser and probe hashes match.

This result supports the measured cross-user signal boundary for disposable command-line children. It does not establish WebKit service identities, browser rendering, physical input, or protection across websites. The browser's confirmed pause bypass remains open.

The administrator authorization covered this single test and is consumed. No further privileged command is authorized. The next experiment uses a separate same-user rendering probe without a window or permission changes.

See [measured evidence](evidence/identity-signal-results.json), [prepared controls](identity-signal-findings.md), and [renderer probe plan](research/renderer-identity-probe-plan.md).


## Milestone 99: same-user headless rendering

Milestone 99 establishes a same-user rendering baseline. A separate hardened diagnostic loads one fixed inline fixture in a nonpersistent WKWebView. It creates no window, posts no input, requests no grant, and refuses root execution. The diagnostic itself is unsandboxed so it can read kernel process metadata. It exposes no external command endpoint.

Three fresh processes pass JavaScript, image, identity, and cleanup checks. JavaScript returns the fresh nonce, an 800 by 600 viewport, and the expected canvas pixel. Each saved PNG measures 1600 by 1200 pixels. Four direct pixel samples match red, green, blue, and white, including opaque alpha.

Two color-accessor changes failed the image check before direct component reads passed. The PNG already contained the expected bytes. The first approach converted colors through AppKit instead of comparing those bytes. Earlier failed calibration results remain in the evidence. This correction changes the measurement, not the renderer.

WebKit creates one invisible TUINSWindow. It never becomes key. The probe creates no explicit NSWindow and observes no visible window. This result does not show that WindowServer access is unnecessary.

Kernel records identify the host and the content, GPU, and network services. Their real, effective, and saved user IDs are all 501. Their group IDs are all 20. Service executable paths and start times remain stable across each snapshot. The private network PID getter can start its service. Its use is explicit in the evidence.

The installed WebKit version is 21624.4.5.11.5. This experiment uses the system framework, not the custom research engine. Session queries succeed and report the console user as 501. Session access alone does not prove correct rendering. The independent JavaScript and image checks supply that evidence.

All measured host and service PIDs disappear after the trials. Two ordinary-user invalid invocations refuse with exit code 64. Frozen browser and probe hashes match milestone 98. No further administrator command ran.

The browser's pause bypass remains open. This baseline supplies no cross-user rendering, protected display, physical input, network compatibility, or general website guarantee. The next ordinary-user step can test a fixed loopback document and image delivery. Any cross-user renderer experiment needs a new reviewed artifact and separate approval.

Run `bash scripts/build-headless-renderer-probe.sh`, then `python3 tools/run_headless_renderer_probe.py --out artifacts/headless-renderer-new`. The output directory must not exist. Keep earlier evidence intact.

See [saved results](evidence/headless-renderer-results.json), [snapshot](evidence/headless-renderer-snapshot.png), and [source research](research/renderer-identity-probe-plan.md).


## Milestone 100: loopback rendering and resources

Milestone 100 adds a fixed loopback mode to the separate headless probe. Its controller owns a temporary server on a randomly assigned local port. It leaves the existing fixture servers unchanged. The native app accepts only the exact main document and child-frame paths for its fresh nonce. It refuses other navigation.

Three fresh network trials pass. Each receives the main document, an image, an iframe, and a fetch response. Independent server receipts record all four requests. The owner script reads matching frame and response nonces and a loaded image width. This script is a diagnostic control, not an external agent action.

Six snapshot samples match red, green, blue, white, yellow, and cyan. The latter two come from the network image and child frame. All six pixels have opaque alpha. The image check reads direct components from the encoded PNG. It accepts the expected aspect ratio at the measured scale.

Three inline regression trials also pass after the shared JavaScript helper changes. In all six trials, kernel records identify stable content, GPU, and network services under real, effective, and saved user ID 501. Each app observes one invisible, nonkey framework window and no visible window. Every JavaScript, pixel, identity, and host cleanup check passes.

All measured host and service PIDs disappear after the trials. The temporary server stops and closes its socket. Three invalid port or option invocations refuse with exit code 64. Swift compiles with warnings as errors. Python compilation passes. No administrator command or permission change occurs.

This result covers one disposable local document and its same-origin resources. It does not establish authentication, cross-origin frames, downloads, video, physical input, cross-user rendering, or protection from agents. The browser's known pause bypass remains open. The current same-user services do not supply a new signal boundary.

Run `bash scripts/build-headless-renderer-probe.sh`, then `python3 tools/run_headless_renderer_probe.py --network --out artifacts/headless-loopback-new`. The output directory must not exist. The controller stops at the first inconclusive trial and preserves its evidence.

See [network and regression results](evidence/loopback-renderer-results.json), [network snapshot](evidence/loopback-renderer-snapshot.png), and [earlier baseline](headless-renderer-findings.md).


## Milestone 101: direct execution and bounded results

Milestone 101 adds an inline-only result transport to the separate headless diagnostic. The probe accepts no URL, script, output path, or network port in this mode. It returns its fixed control report and PNG through stdout. It still refuses execution as root.

Three direct-execution trials pass JavaScript, snapshot, stable identity, and cleanup checks. These launches use the executable directly, without LaunchServices. Each returns a 37,593-byte PNG and records zero explicit snapshot-file writes. The ordinary-user controller saves the image after receipt. Kernel records again show real, effective, and saved user ID 501 for the host and every sampled WebKit role.

The native image limit is two MiB before base64 conversion. The controller stops the stream above three MiB and enforces a 30-second deadline. Four subprocess tests cover the exact byte limit, excess data before EOF, a silent stream, and EOF without process exit. All pass. Every test child exits during cleanup. Three further renderer trials pass through this bounded reader.

A separate loopback regression also passes. The combined pipe/network option refuses before creating an output directory. All measured probe and service PIDs disappear. Frozen browser and permissioned probe hashes match. No privileged command or grant change occurs.

Zero explicit snapshot-file writes does not mean zero framework writes. The unsandboxed host and its XPC services can use OS-managed state. This result does not establish filesystem isolation, another user identity, or protection from process suspension. A hostile agent can still pause a same-user controller or renderer.

The cross-user review identifies unresolved GUI session, cache, shared-account, and auxiliary cleanup questions. No privileged renderer command is ready. The prior administrator approval covered only the completed milestone 98 signal experiment. Do not reuse it for rendering. A later proposal needs trusted staging, permanent credential drops before execution, measured role identities, and an independent watchdog.

Run `bash scripts/build-headless-renderer-probe.sh`, then `python3 tools/run_headless_renderer_probe.py --pipe --out artifacts/headless-pipe-new`. The output directory must not exist. Run `python3 -m unittest discover -s tools -p test_headless_renderer_pipe.py` for the receiver checks.

See [saved pipe results](evidence/renderer-pipe-results.json) and [cross-user feasibility review](research/cross-user-renderer-feasibility-plan.md). Agent-free operation remains unmet.


## Milestone 102: sandboxed host filesystem controls

Milestone 102 adds three separate disposable apps. The reference has no App Sandbox entitlement. The minimal sandbox has only App Sandbox. The network-enabled sandbox also has outgoing-network capability. Every app uses the same fixed inline fixture and bounded stdout transport. None loads an external URL or requests an operating-system grant.

The reference appends a fixed marker to a disposable file outside its container. The controller creates that file with mode 0600 and checks its bytes afterward. The native code rejects symlinks, wrong ownership, and unexpected contents before any write. The sandbox comparison uses the exact absolute path to the same kind of file.

Three fresh reference/network-sandbox pairs pass. Every reference appends its marker. Every sandbox open returns EPERM and leaves its file unchanged. All six apps create, write, read, and remove their own temporary canary. JavaScript, snapshot pixels, stable role identities, and process cleanup also pass. A separate pilot pair passes the same checks.

The minimal sandbox blocks the absolute workspace write and passes its temporary-file control, but WebKit fails to launch its services. Direct execution and LaunchServices both show this failure. No valid snapshot results from those trials. The installed framework reports content termination and role PID zero.

Pinned WebKit checks sandboxed clients for outgoing-network permission or access to a networking service. Its comments identify local-resource support without that access as unfinished. This source is consistent with the measured failure. The distinct network-enabled variant succeeds, but that does not prove the installed framework took the exact pinned branch. See [the source review](research/renderer-filesystem-containment.md).

Earlier pilots exposed two measurement errors. Direct execution inherits a responsibility PID that differs from the host PID. Responsibility therefore does not prove exclusive ownership here. App Sandbox also changes the working directory to its container. A relative canary path returned ENOENT and supplied no denial evidence. The final controls use owner-side role getters, kernel records, and absolute canary paths.

A separate read-only helper checks exact research-host and WebKit executable paths before returning credentials. It samples each identity twice while the app remains alive. Every successful role uses real, effective, and saved user ID 501. Native and external records remain available separately. The helper accepts no command and sends no signal.

Five bounded-reader tests and four metadata-refusal tests pass. Both Swift build modes compile with warnings as errors. The C helper also compiles with warnings as errors. The final apps retain hardened runtime signatures. Frozen browser and permissioned probe hashes match.

App Sandbox creates OS-managed app containers and permits writes there. Those research containers remain as application data. Each app removes its temporary-file control. Workspace canaries remain in the saved trial directories. All measured host/service PIDs exit. This experiment does not audit every framework write or establish identical service sandbox rules.

The known same-user pause bypass remains open. No administrator command ran. Cross-user rendering, inherited session capabilities, shared nobody state, and auxiliary cleanup still need a separate reviewed proposal. The completed milestone 98 approval cannot authorize that future test.

Run `bash scripts/build-renderer-filesystem-control.sh`, then `python3 tools/run_renderer_filesystem_control.py --sandbox-kind NetworkSandbox --out artifacts/renderer-filesystem-new`. The output directory must not exist. The controller stops at the first inconclusive comparison.

See [measured results](evidence/renderer-filesystem-results.json). Agent-free operation remains unmet.


## Milestone 103: cross-user renderer preflight

Milestone 103 adds a separate pipe-only renderer and finite native supervisor. It prepares one exact cross-user inline smoke test, but runs no administrator command. The known pause bypass remains open.

The supervisor loads only libSystem. A fixed staging command checks four copied files before execution. The renderer child permanently drops to the existing `nobody` identity before AppKit or WebKit initialization. A detached watchdog protects only the fork-created child. Root treats output as opaque bytes and never acts on reported service identifiers.

Three ordinary-user rendering trials pass, plus an inherited-signal regression. Watchdog, output-limit, deadline, foreground-group interruption, parent-only death, and closed-output controls pass. Four forbidden invocations refuse. Ten staging tests pass. The final ordinary-user staging rehearsal verifies the exact files, observes the required administrator-mode refusal, and removes staging.

Static review found and fixed a masked dependency-tool failure and cleanup through sealed directories. The final command records the separate supervisor, copy, and tool alarms. The 32-second supervisor alarm does not bound the complete staging command. Outer-shell SIGKILL can leave staging files.

All measured host and role credentials remain user ID 501. No cross-user renderer result exists yet. Framework caches, shared identity state, inherited session capabilities, sampled role identities, and auxiliary cleanup remain limitations. All frozen executable hashes match.

The exact command and manifest are committed with the evidence. The earlier administrator approval is consumed and does not cover this proposed run. Obtain a separate one-run approval before execution. See [findings](renderer-identity-preflight-findings.md), [evidence](evidence/renderer-identity-preflight-results.json), and [run plan](evidence/renderer-identity-reviewed-run-plan.json).


## Milestone 104: cross-user inline rendering

The exact reviewed milestone 103 command runs once after the user's continuation approval. Its supervisor permanently drops the renderer to the existing nobody identity. The fixed inline page passes JavaScript and four image samples. Host, content, GPU, and network kernel records all show real, effective, and saved user/group IDs of 4294967294. Role samples remain stable across the snapshot.

The host and watchdog exit normally. The supervisor reaps both. Independent ordinary-user checks find none of the five measured process identifiers and no staging directory. All frozen hashes match. The ordinary controller still uses user ID 501. No account, service, grant, input hook, or session repair changes.

The one-run administrator authorization is consumed. This rendering smoke test includes no pause attack. Signal denial against actual WebKit roles and controller isolation remain open. The result retains shared-account, cache, inherited-session, and sampled-identity limitations. See [findings](renderer-identity-results-findings.md) and [evidence](evidence/renderer-identity-results.json).


## Milestone 105: calibrated renderer signal actor

A new ordinary-user actor checks the exact fixed probe host, role paths, kernel credentials, and start times before any signal. Three fresh references verify twelve actual pauses and resumes across host, content, GPU, and network roles. Killing the actor during its first stopped target triggers detached recovery. Every measured reference process exits.

Fourteen observer/refusal tests and eleven staging tests pass. The observer binds role arguments to the fresh probe report and readable staged app hashes. It checks only metadata for the root-only supervisor. Root staging verifies that helper's bytes. Process-state samples exclude zombies. Separate POSIX session records distinguish permitted same-session SIGCONT from pause permission.

The prepared cross-user proposal reuses the unchanged root images. It adds one fixed readonly observation log with a write descriptor opened before sealing. Root never acts on reported service identifiers. The exact ordinary-user staging rehearsal passes and administrator mode refuses. Default staging still reproduces the original milestone 103 command hash.

No new administrator run occurs. The earlier one-run approval covers the completed milestone 104 smoke test only. A new one-run approval remains necessary. This test covers signal permission and sampled state, not post-attack page progress. Controller isolation, input, presentation, navigation, broader compatibility, and agent-free acceptance remain open. See [findings](renderer-signal-preflight-findings.md) and [evidence](evidence/renderer-signal-preflight-results.json).


## Milestone 106: inconclusive cross-user signal attempt

The reviewed command runs once after the user's continuation approval. The normal observer reads the fixed report and checks app hashes. Its actor returns code 65 before signal output. It sends no signal. This is an inconclusive attack, not a protection result.

Rendering, image samples, and nobody credential checks pass. The supervisor reaps the normally exited host and watchdog. Independent checks find none of the five measured process identifiers or the staging directory. All frozen hashes match. Later commands use user ID 501.

The one-run administrator approval covers only this completed attempt. No retry occurs. The actor needs operation-specific diagnostics and a cross-user-compatible metadata reader. See [findings](renderer-signal-results-findings.md) and [evidence](evidence/renderer-signal-results.json).


## Milestone 107: cross-user-compatible diagnostic metadata

A readonly comparison reproduces the old reader's cross-user API limitation. BSD info refuses init metadata with EPERM. The separate sysctl and path APIs succeed. The real actor-reader regression fails before the fix and passes afterward.

The actor now reads the SDK process structure, validates its shape, and preserves all six credentials, start time, and exact path checks. A second identity sample brackets the path read. Initial failures name the operation before any signal. Stopped and zombie states refuse. This is a diagnostic SPI, not a production security contract or an atomic process handle.

Three fresh same-user comparisons verify twelve stops and resumes. Parent-death recovery passes. Fifteen observer/refusal tests, eleven staging tests, and the native metadata regression pass. The final actor hash matches the calibrated binary. Root images and the per-launch administrator command remain unchanged.

The new proposal caps comparisons at three serial launches and stops after any failure or inconclusive result. Each invocation consumes an attempt. Verify the helper's exit, rendering, actor outcomes, process exits, and staging removal before another launch. No administrator command runs in this milestone. Fresh approval remains necessary. See [findings](renderer-metadata-findings.md) and [evidence](evidence/renderer-metadata-results.json).


## Milestone 108: measured cross-user signal denial

All three approved serial comparisons pass. The ordinary user attempts twelve SIGSTOP and twelve SIGCONT calls across host, content, GPU, and network roles. Every call returns EPERM. Target identities remain stable and no target enters a stopped state. The calibrated same-user references previously allowed the same actor to stop and resume all four roles.

JavaScript, image samples, nobody credential checks, and helper exits pass. Each supervisor reaps its host and watchdog. Independent checks find none of the fifteen measured process identifiers. All three staging directories disappear. Frozen binaries and approved input hashes match. Later commands remain user ID 501.

The three-invocation administrator approval is consumed. No further administrator run occurs. Post-attack page progress remains unmeasured. The ordinary browser does not integrate the cross-user boundary, so its pause bypass remains open. See [findings](renderer-signal-denial-findings.md) and [evidence](evidence/renderer-signal-denial-results.json).


## Milestone 109: browser navigation controls

Forward, history availability, Reload/Stop, and page-load feedback now work in browser source. The address updates at document commit. Errors use the window subtitle, so the protection footer retains its status. The ordinary shell adds Command-L. The device experiment retains its physical keyboard route.

A separate hidden diagnostic uses the actual controls against a disposable local server. All ten checks pass, including Stop, failed-response feedback, and recovery. The server records the expected routes. Every measured host and WebKit process exits. The initial timing failure remains in the evidence. The control now waits for the slow response before Stop.

Policy checks and device-source type checking pass. All five frozen binaries and the active comparison inputs match their hashes. No privacy setting, input hook, or root code changes. This functional result makes no external-agent protection claim. The known pause bypass remains open.

Milestone 108 remains pending macOS authentication for the first approved comparison. See [navigation findings](browser-navigation-findings.md) and [evidence](evidence/browser-navigation-results.json).


## Milestone 110: post-attack progress calibration

A separate fixed inline diagnostic emits readiness, then runs a fresh page challenge and snapshot after the ordinary-user actor. One baseline and three references pass. All twelve pauses and resumes calibrate across host, content, GPU, and network roles. CLOCK_MONOTONIC ordering places every page sample after actor completion.

The timer advances, the DOM returns its fresh challenge, and the canvas changes from blue to yellow. Role identities remain stable. All sixteen measured host and service identifiers exit. Recovery watchdogs are reaped. Forty-four Python checks, a native readonly metadata regression, and seven invocation refusals pass.

The five frozen binaries and earlier root images remain unchanged. No administrator command or privacy setting changes. Cross-user progress and browser integration remain open. See [findings](renderer-progress-control-findings.md) and [evidence](evidence/renderer-progress-control-results.json).


## Milestone 111: cross-user progress preflight

A separate supervisor profile binds the existing finite lifecycle to RendererProgressProbe. One ordinary-user baseline and three supervised references pass. All twelve pauses and resumes calibrate. The page completes its fresh challenge and yellow redraw afterward. The host and watchdog are reaped, and all twenty measured process identifiers exit.

The readonly observer starts the ordinary actor from the verified readiness report. The comparison controller requires helper exit zero, pause denial, correct credentials, ordered progress, stable roles, and independent cleanup. Its administrator command has a separate pinned hash. Fifty-five Python checks pass. The ordinary staging rehearsal verifies the new images, observes code 64 for administrator-mode refusal, and removes staging.

The one-run proposal remains unexecuted. It changes the reviewed images, so the earlier consumed approval cannot authorize it. All frozen binaries and earlier root images remain unchanged. The 32-second supervisor deadline and earlier cache, session, and interrupted-staging limits remain. See [preflight findings](renderer-progress-preflight-findings.md), [evidence](evidence/renderer-progress-preflight-results.json), and [reviewed plan](evidence/renderer-progress-reviewed-run-plan.json).

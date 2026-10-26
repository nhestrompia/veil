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

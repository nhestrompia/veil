# Current research state

Milestone 124 completes both hosted-media controls. The user sees text and colors on the clear left panel and black on the protected right panel in both H.264 and uncompressed NV12. The reports precede capture. Window captures recover each clear marker and omit each protected marker. Neither path passes physical visibility. All three media test hosts are absent. No physical question remains pending. See [standalone findings](protected-layer-findings.md). Next, combine physical webpage visibility with the existing window-sharing compositor controls, without protected media.

The first paired test timed out before the user could inspect it. Its host is absent. A fresh unchanged app runs as PID 42742. Native window metadata confirms one on-screen window. The pending physical check now refers to artifacts/protected-layer-124/hosted-h264-reopened.

Milestone 124 opens one standalone hosted-H.264 clear/protected pair. It contains no WebView, network, input observer, or permission request. Both panels enqueue samples and report ready output without errors. The physical RIGHT-marker observation is pending. Do not infer visibility from those flags. No screenshot ran during the initial observation period. See [standalone findings](protected-layer-findings.md). The app terminates after ten minutes, with an eleven-minute native alarm backup. Session metadata and private markers live in artifacts/protected-layer-124/hosted-h264. All seven frozen images retain their hashes.

Milestone 123 confirms physical black output in both the source-only clipping diagnostic and the unchanged original H.264 protected app. The original app also fails a solo retest after every other research host exits. The earlier readability report is not reproducible. The clear control remains visible. See [presentation findings](pixel-compositing-findings.md). No physical agent-free baseline exists. The explicit clip moves to a separate source sibling only in a diagnostic build. Do not rebuild the permissioned browser. All five owned test hosts and fixtures stop, and independent process reads find none of those hosts. No further physical question is pending.

Milestone 122 confirms the grant through LaunchServices, but the physical protected page is black. The clear control is visible and completes one internal task. The protected session receives physical navigation and keys but completes no action. See [physical findings](pixel-keyboard-physical-findings.md). Keep the permissioned browser frozen. Source clipping and frame layout need isolated diagnosis. Bounded sessions remain open until their original deadlines.

The user then authorized this grant in Settings. The readable pane listed DeviceKeyboardExperiment and HIDObservation, but omitted PixelKeyboardExperiment. The Add click returned `windowNotFoundAtPosition`. Settings then appeared dimmed. The tool did not show an authentication prompt. A system-dialog observation stalled for 1261 seconds despite its 20-second timeout. The unchanged app still reports `listenGranted=false`. Neither the grant nor the app addition has confirmation. Native UI control cannot complete this step.

The user approved the exact PixelKeyboardExperiment Input Monitoring request. The request ran through LaunchServices and exited zero. The unchanged binary still reports `listenGranted=false` after the request and on a later read. The earlier automatic approval rejection is resolved by this consent.

System Settings returns `cgWindowNotFound` on two UI attempts. Opening the Input Monitoring pane succeeds, but the UI tool cannot read its window. No switch, reset, re-add, authentication, or other grant change occurs. The user must enable this app in that pane before physical tests can proceed. Do not claim that the Mac is locked from this error.

Keep the manifest-pinned app unchanged. The next tests require physical navigation and form completion, then external attacks against the same loaded session. No physical baseline or new attack result follows from the permission request.

Milestones 120 and 121 complete an external agent audit and prepare a combined protected-pixel keyboard browser. The audit finds a real launch-URL action bypass in the old pixel app. The new PixelKeyboardExperiment prefills that URL and waits for device binding and Return. Its final launch comparison records no page-ready event or action. See [the attack audit](pixel-agent-audit-findings.md), [combined findings](pixel-keyboard-findings.md), and [route inventory](agent-attack-inventory.md).

The compile-time routing control completes exactly one form action through process-local keys. It is not a physical baseline. The protected image excludes that generator. Its address editor and WebView stay outside clipped window bounds; their pixels reach the protected media producer. No mouse bridge exists.

Playwright/CDP completes a task in isolated Chrome. Native debugging-port attempts refuse. The new host's AX tree exposes only its root. Its direct AX and screenshot checks fail calibration and remain inconclusive. The old pixel app's capture results do not prove capture protection for this new combined image.

The new app still reports Input Monitoring off after the approved request. Keep the [manifest-pinned images](evidence/pixel-keyboard-permission-manifest.json) unchanged through consent and physical tests. The original five permissioned images remain frozen. No input hook, device seizure, administrator access, or unrelated-process change occurs. Existing modifying mouse hooks still prevent safe synthetic input tests.

Milestone 119 adds a separate H.264 producer pair after a detailed Antiagent evidence review. Three encode/decode frames and changed-size refusal pass. Two paired comparisons recover the control marker through three routes and omits the protected marker. Unfiltered compositor capture refuses the missing owned backdrop. The user reports a readable page on the physical display. No exact marker was supplied. Same-process follow-up captures omit the page through three routes. See [compressed findings](compressed-rendering-findings.md).

The encoder hardware readback is unsupported on this Mac. Hardware remains required at session creation. Hardware decoder readback passes in the round-trip check. No capture guarantee follows from these checks. Five frozen permissioned images retain their hashes. No new grant, hook, or administrator action occurs.

Bounded exec session 75457 finished and stopped its app and fixture. The delayed computer-use call opened an empty app after the trial. That invalid observation adds no capture result, and the empty owned instance was stopped. No observation question remains pending.

The final smoke-fixture correction changes app hashes but not rendering code. The codec and paired capture checks pass on the final images. The physical readability report applies to the earlier rendering-identical image. Unfiltered display and continuous capture, transitions, and input remain open. Preserve this useful result without claiming general screenshot protection.

Current focus: screenshots, scripts, accessibility, and input. See the [route research](research/agent-access-routes.md). A file watcher misses capture in memory.

The mouse pilot is offline. No keyboard classifier exists. Both protected layers hid the page from the person. Prioritize visible protected output and direct automation checks. The user authorized no new privilege.

Milestone 116 completes the approved single cross-user channel comparison. All four renderer SIGSTOP and four SIGCONT calls return EPERM. The ordinary-user display still stops and resumes successfully. During its pause, the isolated renderer completes eleven fresh page-and-image samples and advances its timer from six to seven. Fresh display output resumes, one stale frame refuses, and sampling continues after peer exit. See [live findings](renderer-channel-live-findings.md).

All 23 comparison checks pass. Both app hosts and the native watchdog are reaped. Signal actors reap their recovery watchdogs. Independent checks find none of seven measured process identifiers and no staging directory. Five frozen permissioned binaries and every reviewed input retain their hashes. The ordinary controller remains user ID 501.

The one-invocation administrator allowance is consumed. Its exclusive ledger is artifacts/renderer-channel-115-authorization-consumed.json. Unified exec session 4815 completed with exit zero. No authentication or permission question remains pending. Do not rerun the command or use this allowance for another root action.

The user requested a clear explanation of why agent-free browsing remains unmet. The [gap audit](agent-free-gap-audit.md) records unfinished integration, complete physical input, non-input action routes, unresolved visible-output privacy, and final same-build validation. The current two-process target is hidden, fixture-only, and has no human input route. The earlier physical keyboard browser remains separate. Do not describe this result as a delivered agent-free browser.

No further privilege, grant, account, service, or input-hook change occurs. The next engineering deliverable is one visible, human-usable integrated prototype. Capture privacy remains open research. Root attacks and modified binaries remain outside the existing PoC scope.

Milestone 115 calibrates the separate channel supervisor and prepares one unexecuted cross-user proposal. Three final-image comparisons pass. Twelve renderer stops and resumes and three display stops and resumes calibrate. The renderer completes 11, 11, and 11 samples entirely during display pauses. Native lifecycle and fault controls pass. All 72 measured process identifiers exit. See [preflight findings](renderer-channel-preflight-findings.md).

All 78 Python checks pass, plus the native readonly metadata regression. Clang static analysis reports zero diagnostics. The ordinary-user staging rehearsal verifies the real images, observes administrator-mode refusal with code 64, and removes staging. The final images contain no loader search path. Earlier loader-bearing images remain only as an earlier ordinary control result.

The [exact proposal](evidence/renderer-channel-reviewed-run-plan.json) covers one administrator invocation. It stages seven verified images, creates two app children, and permanently drops them to nobody and ordinary user ID 501. A finite root parent and watchdog protect only those known app hosts. No root process acts on reported WebKit identifiers. The apps stay hidden and use one fixed disposable loopback fixture.

No new administrator command runs during preparation. All earlier root allowances are consumed. This changed helper requires separate one-run approval. No macOS authentication dialog is pending. Keep the reviewed images and source hashes frozen. The controller pins the full plan and command, and records consumption before requesting authentication.

Five frozen permissioned executables, earlier privileged images and actors, and milestone 113 and 114 images remain unchanged. No grant, hook, account, service, or visible window changes. Auxiliary cleanup after interrupted trials, shared nobody state, framework caches, and inherited capabilities remain limits. The native alarms do not bound authentication or the entire staging command.

After approval, the single comparison can measure renderer pause denial alongside a permissioned display pause and continued private pixels. Cross-user operation remains unmeasured now. Physical input, original HID timestamps, private visible presentation, broader websites, and normal-browser integration remain open. Agent-free operation remains unmet.

Milestone 114 passes native descriptor handoff under ordinary user ID 501. Three hidden page/display controls pass, including inherited ignored and blocked signals. Deadline, output-limit, stalled-startup, parent-death, group-termination, and closed-output controls pass. Six forbidden invocations refuse. All 45 measured process identifiers exit. Auxiliary WebKit cleanup coverage remains incomplete after interrupted trials. See [launcher findings](renderer-channel-launcher-findings.md).

The native launcher owns both fork-created app hosts. It gives each child one socket endpoint and arms a detached watchdog before execution. It starts the display only after renderer readiness. A bounded report pipe carries diagnostic output. The watchdog targets only verified host identities. Root is refused. No privilege, grant, hook, visible window, or existing app image changes.

Clang static analysis reports zero diagnostics. The first collector pilot remains inconclusive despite its successful native result. The final repaired matrix passes. Five frozen permissioned executables, earlier privileged images, and all milestone 113 diagnostic images retain their hashes.

Next, prepare a separate cross-user launcher or isolated coordinator with secure staging and finite cleanup. The ordinary-user launcher is a control, not a protected enrollment path. Original HID timestamps, physical input, private presentation, general websites, and other action channels remain open. The current browser still has its confirmed same-user pause bypass. Agent-free operation remains unmet.

Every earlier administrator allowance is consumed. No authentication or permission question remains pending. No new privileged command is prepared or authorized by milestone 114.

Milestone 113 passes three private-channel comparisons and one pause-helper recovery trial, all under ordinary user ID 501. A paused display stalls the blocking reference for about 1.2 seconds. The nonblocking renderer completes 11, 12, and 11 page samples entirely inside those pauses. Fresh images resume, expired frames refuse, and page samples continue after peer exit. All 42 measured process identifiers exit. See [channel findings](renderer-channel-findings.md).

The channel uses an inherited anonymous socket pair, bounded messages, session framing, expiry, and one replaceable pending frame. No listener or token file exists. The hidden display proves image decoding and assignment only. Software sends initial navigation. Session possession does not establish human origin or secure peer enrollment. Cross-user channel wiring and physical input remain untested.

All 257 channel checks pass in optimized and Address Sanitizer builds. The native readonly metadata regression and 55 existing Python checks pass. The failed polling pilot remains visible. Five frozen permissioned binaries, earlier privileged images, and earlier signal actors retain their hashes. No new administrator command, grant, visible window, or input hook runs.

Next, prepare cross-user channel integration while preserving the existing identity boundary and finite cleanup. Original HID timestamps must reach the input receiver before expiry can address delayed hardware events. Keep permissioned apps frozen. General website compatibility, physical pointer input, privacy gaps, and other action channels remain open. The current ordinary browser still has its confirmed pause bypass. Agent-free operation remains unmet.

Milestone 112 passes its approved single cross-user progress comparison. All four SIGSTOP and four SIGCONT attempts return EPERM. A fresh JavaScript/DOM challenge, timer increase from three to nine, and yellow redraw pass afterward. The helper exits zero, both children are reaped, and all five measured process identifiers and staging disappear. See [progress findings](renderer-progress-findings.md).

Every earlier administrator allowance is consumed. No authentication or permission question remains pending. Do not rerun a privileged comparison under an earlier approval. Future privileged experiments require a new concrete proposal. Milestone 113 runs entirely as the ordinary user.

Milestone 108 now passes all three approved serial comparisons. All twelve SIGSTOP and twelve SIGCONT calls return EPERM for the cross-user host, content, GPU, and network roles. JavaScript, image samples, identity checks, helper exits, and cleanup pass. None of the fifteen measured process identifiers or three staging directories remain. Frozen binaries and approved input hashes match. See [signal-denial findings](renderer-signal-denial-findings.md).

Unified exec session 2537 is complete. All three invocation allowances are consumed. No authentication or permission question remains pending. Do not launch another administrator command under that approval. Root remains limited to the completed reviewed experiment. Future privileged work needs a separate concrete proposal.

Post-attack page progress remains unmeasured. The ordinary browser does not integrate cross-user rendering, and its pause bypass remains open. Next, prepare a bounded progress comparison with same-user calibration before any new privileged proposal. Controller isolation, private input and presentation, and broader compatibility remain open. Agent-free operation remains unmet.

Updated 2026-10-26. Milestone 58 confirms an external focus-only action bypass in three fresh diagnostic processes. Activating another research window and returning completed one new action in each candidate. The standalone helper posted no input and made no AX call during those cycles. The gate admitted zero keyboard events. Agent-free operation is unmet.

Milestone 59 tested separate AppKit activation filtering and logical key-window state. Both stopped the original focus action and preserved private typing. Both failed a visibility-change action when an agent hid and restored the app. The final filter comparison reproduced two new actions in each of three candidates. No input was posted or admitted. The password control could not switch away and remains inconclusive. Temporary cleanup restored Secure Event Input to off. All 87 Python checks pass. See [lifecycle findings](lifecycle-findings.md).

Neither diagnostic option is enabled in production. Milestone 60 restores embedded about:blank and about:srcdoc navigation while retaining top-level restrictions. All nine editor/frame baselines passed. The repeated matrix produced 27 native blocks and 18 inconclusive cases. Every temporary process passed cleanup. See [embedded-document findings](embedded-document-findings.md). A general lifecycle solution remains open. WebKit reads focus and visibility independently. Any further state experiment must preserve password deactivation and input cleanup. See [focus research](research/focus-boundary.md).

The earlier milestone 58 page matrix blocked 21 native attempts across seven working private baselines. Fourteen cases remain inconclusive. A fresh textarea retry passed; the first failure remains unexplained. The earlier srcdoc failure is repaired by milestone 60 below. All 85 Python checks pass. See [page findings](page-feature-findings.md).

The feature fixture runs on port 8766 with its own controller file. The original fixture and physical browser PID 61893 remain unchanged. No temporary research process remains. Keep the frozen physical browser and permissioned probes unchanged. New policy and focus results belong to separate diagnostics.

Milestone 61 adds only a stable-activity diagnostic. It stopped matched visibility, blur, and password focus actions in one fresh process per mode. Private typing resumed in all three. Its password candidate recorded aggregate Secure Event Input on while hidden, unlike the readable control. WebKit ownership is a source-backed inference; another foreground app was not established. Every cleanup succeeded and left Secure Event Input off. Do not enable this host getter policy in production. See [stable-activity findings](stable-activity-findings.md).

Milestone 62 chooses the next research boundary after three sketches and an independent judge. Preserve native UI-process state and project five flags only at content serialization and page creation. Keep native ownership on actual AppKit state. Use immutable configuration, with no authorized activity-commit API. See [the design and gates](research/activity-boundary-plan.md) and [grounding](research/activity-grounding.md).

Milestone 63 implements the isolated engine patch under engine/. Twelve source files are pinned by hash. The generated six-file patch applies exactly, with zero fuzz. Its configuration choice is captured as a constant in WebPageProxy. Both known outgoing sites project all five flags. Native activity calculation and Secure Event Input code remain unchanged.

The actual projection header compiles against the exact enum declaration extracted from the pinned header. All 65,536 flag combinations pass both modes, including nonprotected flags and idempotence. This standalone check does not compile WTF OptionSet, WebPageProxy, Cocoa, or the full engine. All 89 Python checks pass. See [engine reproduction](../engine/README.md) and [saved evidence](evidence/engine-projection-results.json).

Next, inventory full sender/receiver and ownership paths, prepare a bounded source/build plan, and build a separate research engine. Milestone 64 downloaded and checked the full pinned source. It remains pristine, unpatched, unbuilt, and unexecuted. Xcode 27.1, Metal, 32 GiB RAM, 10 logical CPUs, and about 204 GiB free passed read-only checks. Keep build outputs inside the workspace and preserve an OS disk reserve. Verify app and content-process loaded identities before runtime claims.

The OpenCode/DeepSeek judge failed before execution because its configured key expired. Do not retry credentials. A separate native judge completed the review. The original architectural workflow proceeds without a human checkpoint. An editor-state protection barrier and every native owner path remain implementation gates. Keep the frozen physical browser and probes unchanged. Default InternalKeyboardControl was restored without logical getters; no temporary research app remains, and Secure Event Input is off.

## Current priority and remote control

The user clarified that recognizing physical typing is separate from agent-generated input. Do not count that observation as an autonomous input bypass. Prioritize navigation and website actions by external agents. Keep confidentiality results separate.

Safari Web Inspector read the reference marker and completed one accepted task. The working reference appeared in the Mac target menu, while the unchanged candidate did not. This is a not-advertised result, not a direct attachment refusal. See [remote findings](safari-remote-findings.md).

The user approved a temporary developer-setting toggle and restoration. The UI confirmed its final state was off. Research Safari windows closed and the reference passed cleanup. A broader inspection-list read was rejected because of unrelated tab URLs. The safer Mac-only menu completed discovery.

DockDoor and LinearMouse had restarted. Their verified processes stopped before input, and the safeguard then reported no blocking hooks. Recheck before every later attack.

## Renderer helper

The user approved RendererAXProbe Accessibility. Its effective grant is true. Its executable SHA256 is `82d0c15dadfa49d1669a576270c08cb9b749d6fe102b1724fa61f6dd2d9b08a7`. It installs no input hooks. It checks exact research paths, process start times, and OS responsibility before reads.

Two direct-root references failed. Host initialization changed the renderer root from unavailable to AXApplication, with no controls or marker. Candidate AX queries were skipped. All cleanups passed. See [renderer root findings](renderer-root-findings.md).

Three token references recovered their own markers. Three matched candidate reads recovered no marker or fixture controls within IDs 0 through 1,023. Candidate actions were skipped because the fixture URL guard prevented reference actions. Read and action calibration are now separate. See [token findings](renderer-token-findings.md).

The user approved renderer-only off/on, exact-bundle re-add, and an app-only Accessibility reset if needed. Off/on failed. The reset succeeded. System Settings needed a normal restart before its Add button enabled. Exact-bundle Add restored effective access. No permission question remains pending. The scope excludes other apps and global resets.

Three native host references completed external Reload actions with matching page-ready events. Three matched candidate scans found no address field or Reload button within IDs 0 through 1,023. No candidate action was sent. All cleanups passed. See [host navigation findings](host-navigation-findings.md). Other IDs and directly addressed actions remain open.

The user authenticated the latest approved exact-bundle re-add. Effective Accessibility is true. No permission question remains pending. Keep the current helper frozen. Milestone 56 repeated native input and semantic tests on PID 61893. Twenty-nine native attempts were blocked; twenty-two cases remain inconclusive. No accepted input or new website action appeared. Three semantic comparisons passed their reference controls; candidate targets were unavailable. See [current session findings](current-session-attack-findings.md).

The new controller checks foreground activation before window geometry. An earlier setup run sent no candidate input and stopped with cleanup. The follow-up repaired activation for both references and candidate. Keep failed and skipped cases visible. Final checks found no temporary reference or probe processes. The browser and fixture remain running.

Frame and editor coverage now has the milestone 58 results above. Separate diagnostics contain the new configuration. They require no new permission. The source policy disables passkeys, native sharing, asynchronous clipboard, Apple Pay, Writing Tools, and element fullscreen. Three valid interface controls passed. Native selection export remains inconclusive because its readable control returned empty data. One private authorized keyboard task passed. See [content policy findings](content-policy-findings.md). Do not attribute new-source results to the frozen physical browser.

Remaining action priorities include failed PID-directed mouse calibration, direct inspector attachment beyond discovery, exports, session reuse, and broader website compatibility. Unfiltered capture on this physical build remains separate. No permission question is pending.

## Keyboard confidentiality result

The external observer matched the fixed fake phrase through both Unicode and virtual-keycode matchers. It received sixteen events while the restricted browser accepted one requested physical task. The controller generated no input. Device binding and unchanged identity were confirmed. The listener stopped on focus loss, removed its tap, and passed cleanup.

The current generated reference matched both decoders and completed one task. It is not a physical reference. This would limit negative conclusions, but the candidate observation was positive. See [the readiness findings](keyboard-readiness-findings.md) and their saved evidence.

Earlier physical attempts remain inconclusive. Their observer deadlines started too early. Earlier PIDs 43980 and 58504 stopped without a matching crash report. Their exit causes remain unknown. Do not attribute their completed attack matrices to the new PID.

## Live session and frozen identities

The capture-restricted browser is PID 61893. Its session file is `artifacts/source-policy-live/keyboard-observation-ready-session.json`. The fixture and caffeinate remain in unified exec session 53557. No observer or controller remains active. The empty replacement readable control was closed with exact executable verification.

- Browser SHA256: `43b1a9833d6c55b1e254b848f9bd09c202da46ba0f8d8833084df559e6a8a9d1`.
- NativeProbe SHA256: `7c256598528dcaf2dcdc6437af30dab92d9c4ca929a55a3a2402f09754f67de1`.
- KeyboardObservationProbe SHA256: `cdd1829e60dd838f5a2b1ef91f9d5635e7f61760360f9c18c494f8eb90086aac`.

Keep these executables frozen during matched tests. The observer has effective Accessibility and listening access. The user approved its exact Accessibility Add and its app-only reset followed by re-add. No other permission reset follows from that approval. No permission question is pending.

To stop the exact browser:

```sh
python3 tools/run_device_session.py stop --session artifacts/source-policy-live/keyboard-observation-ready-session.json
```

Stop the fixture separately when live work ends.

## Completed boundaries and remaining work

The older physical process refused 27 calibrated native attempts and three adaptive vision attempts. Its input matrix does not replace the current-process evidence above. Window and filtered-display images were black. System screenshots and unavailable AX actions remain inconclusive. Fifteen startup comparisons and eighteen session-insertion refusals are separate diagnostic results.

The current observation disproves keyboard confidentiality against this permissioned listener. The generated password comparison received no keys during two accepted tasks. Secure input was active, and cleanup restored its inactive state. Physical password entry remains untested. See [the secure-entry result](secure-entry-observation-findings.md). Apple TN2150 advises against enabling Secure Event Input for general text or an entire app lifetime. Do not turn that into a whole-browser fix without a separate design and compatibility experiment.

Direct remote attachment beyond discovery, unfiltered capture on this physical build, renderer semantics, broader session privacy, and general website compatibility remain open. The browser supports only the measured built-in keyboard and US ASCII. Pointer input is disabled. The device policy does not attest a human or cryptographically attest hardware.

All 82 Python checks pass. Swift matcher, timing, and renderer-boundary checks pass. See [implementation milestones](implementation.md) for the full record.

## Desktop safeguards

Check effective permissions and `desktopInputSafety` before input. Refuse unavailable checks or modifying mouse hooks. Never install modifying global taps, seize devices, reset global TCC state, kill tccd, or bypass guards.

The earlier click failure cleared after DockDoor stopped. Its exact cause remains unknown. Do not reproduce it. The browser reader is non-seizing and routes keys only while its window is key and frontmost.

The observer uses a PID-scoped listen-only key-down tap. It decodes only while the exact research target owns focus. It saves no raw text or key codes. The first key starts a fifteen-second sample after at most sixty seconds of idle wait.

Do not select the AX-hidden browser through computer use. That path stalls. Refresh computer-use documentation before UI work. Selecting a closed readable control can create an empty replacement window. Verify exact process identity.

No branch was pushed and no pull request was created. The historical pause note below concerns earlier builds.

---

# Research paused

Paused at the user's request on 2026-10-24. Do not resume tests without a new instruction. The local fixture and its keep-awake process stopped. No project research application remained during the final cleanup check.

## Current result

The browser is not proven agent-free. The native probe's existing grants and the browser's existing Input Monitoring grant were refreshed through System Settings. No new permission scope was added.

Milestone 29, commit `9382485`, restored native calibration. Nine of eleven reference routes completed their task. Two PID-directed mouse routes remain inconclusive. The native runner now skips candidates without successful matched references.

Milestone 30, commit `c1c40e7`, added paired legacy HID releases and hardened startup-test cleanup. All 25 Python checks pass. Fifteen references completed their task, and fifteen matched fresh-start candidates admitted no input or website action. Every candidate had a ready device reader, with no binding observed. Every process passed cleanup. This does not establish usability after physical binding or hardware attestation.

## Capture milestone completed before pause

The controller now also tests the system screenshot tool against the exact research window. The capture runs finished before the pause request.

| Route | Readable references | Restricted diagnostics |
| --- | --- | --- |
| ScreenCaptureKit stream with an owned backdrop | Marker recovered in 3 of 3 | Marker absent in 3 of 3. Research backdrop recovered in all three. |
| ScreenCaptureKit window image | Marker recovered in 3 of 3 | Marker absent in 3 of 3 captured images. |
| System window screenshot | Marker recovered in 3 of 3 | All three capture commands failed. These are inconclusive results. |

All twelve diagnostic processes completed one internal form action. These are private bootstrap controls, not physical-human controls. The latest restricted binary still needs physical visibility and usability evidence before any agent-free claim.

Raw results are under `artifacts/capture-after-recovery/`. The four directories are `visible`, `restricted`, `window-visible`, and `window-restricted`, each with trials `0` through `2`. The first two contain stream runs. The other two contain window and system screenshots.

## Desktop safety

The earlier physical click failure cleared after DockDoor stopped. Stopping the computer-use service and LinearMouse alone did not clear it. The exact interaction remains unexplained. Do not reproduce that failure on the user's desktop.

LinearMouse restarted during later work. The new guard refused input before launching a browser. A normal quit followed by an immediate bounded trial isolated the input path. Recheck active hooks before future input. Do not silently bypass the guard.

The diagnostics have termination timers, and controllers verify exact executable cleanup. Native CGEvent and legacy HID adapters release their own pending input after errors. Forced process termination still cannot establish an absolute input-release guarantee.

## Resume points

1. Read this note and use `but diff` for pending changes. Raw Git index status is stale under this GitButler workspace.
2. Confirm the current probe hash, effective grants, console access, and mouse-hook status. Rebuilding the probe can invalidate its grants.
3. Calibrate references with the exact current probe before candidate attacks. Earlier reference hashes cannot replace new calibration.
4. Continue same-process attacks after a valid physical binding. Physical usability on the latest restricted build remains unverified.
5. Keep Safari inspector attachment and adaptive mouse-behavior research separate. Neither has a completed result in this pause milestone.

The final diagnostic build in `dist/InternalKeyboardControl.app` is capture-restricted, without the full-screen backdrop. It has a private startup sequence and no physical device reader. `DeviceKeyboardExperiment.app` remains the separate keyboard-only research browser.

No branch was pushed and no pull request was created during this session.

## Milestone 64 source preparation

The isolated source dependency retains about 1.8 GB and preserves a 60 GiB disk reserve. All twelve pinned hashes and pristine reuse pass. All 92 Python checks pass. The archive returned HTTP 422, so preparation uses a shallow sparse dependency clone. See [the source audit](research/activity-full-source-audit.md) and [evidence](evidence/engine-source-results.json).

The audit covers live updates, creation, remote pages, process swaps, and recovery. Independent initial-focus operations remain outside the patch. WebKit exposes a private per-view ownership readback. Next, measure that flag in matched password diagnostics, then apply and build the isolated patch. Always set WEBKIT_OUTPUTDIR inside the workspace before upstream build scripts.

## Milestone 65 direct owner readback

One ordinary and one stable-host password comparison passed. The stable host retained its own WebKit ownership flag while hidden, with another research app foreground. The ordinary host released it. Both resumed one private task. The ordinary focus-only bypass reproduced. Cleanup passed and aggregate Secure Input returned to off. See [ownership findings](secure-owner-findings.md). The default diagnostic was restored. The engine source is still unpatched and unbuilt.

## Milestone 66 isolated engine build

The six-file patch is now applied to the separate pinned checkout. Exact hashes and retry checks pass. All 95 Python checks pass. The first build stopped before compilation because Configurations was missing. The source list and dependency scheme are corrected. The second attempt started real compilation with four jobs at reduced priority. A 60 GiB disk reserve and two-hour limit apply.

Build receipts and logs are in .build/webkit-engine/. No completed engine or runtime result exists yet. Preserve the running build monitor. Verify actual UI and content-process framework identities before any live claim. See [build instructions](../engine/README.md).

## Milestone 67 engine identity gates

The engine diagnostic compiles. A system-framework fallback refused before window creation. All 99 Python checks pass. Positive UI and content mapping checks remain untested against a completed custom engine. The prepared InternalKeyboardControl now uses the engine-stable variant and an ad hoc signature without hardened runtime. Do not launch it as an ordinary control. Frozen browser and probe binaries remain unchanged.

The second build stopped at Metal shaders. Apple MetalToolchain 27A266a is now installed and its compiler executes. The third incremental build runs with quiet logs and a macOS 26 deployment target. Its monitor PID is in .build/webkit-engine/build-results.json. The active unified exec session is 67320. Preserve that monitor and its disk reserve. See [runtime findings](engine-runtime-findings.md).

## Milestone 68 child-frame controls

One matched ordinary comparison each reproduced a focus-only action in same-origin, cross-origin, and srcdoc child documents. Every private baseline and resumed task passed. The helper posted no input during each activation cycle. Cleanup passed and aggregate Secure Input was off. All 99 Python checks pass. See [child-frame findings](child-frame-findings.md).

The prepared InternalKeyboardControl is now the ordinary capture-restricted variant with private resume and ownership logging. The feature fixture restarted on port 8766 in exec session 65052. Its previous controller key is obsolete. Preserve the failed srcdoc setup separately from its successful retry.

## Milestone 69 temporary-directory build correction

The third build failed at Mach interface generation. The assigned shared TMPDIR was denied by Xcode script sandboxing. The actual sandbox profile rejects that path and permits TARGET_TEMP_DIR. Passing TMPDIR as the per-target Xcode setting fixes the narrow WTF target. All four generated files exist. Script sandboxing remains enabled. See [temporary-directory findings](engine-temp-findings.md).

The fourth full build is active in unified exec session 36677. Its monitor and process-group PIDs appear in .build/webkit-engine/build-results.json. Preserve the monitor and disk reserve. The complete engine and all custom-engine runtime claims remain unverified.

## Milestone 70 Swift cache experiment

The fourth build reached Swift tasks but reported zero-exit/no-output failures. Its monitor stopped through scoped cleanup. A narrow JavaScriptCore target passed with compilation caching disabled and linked its framework. The fifth full build uses the narrower SWIFT_ENABLE_COMPILE_CACHE=NO setting. C++ caching remains enabled. The complete engine is still unverified. See [cache findings](engine-cache-findings.md).

The active full-build exec session is 72341. Preserve the monitor and disk reserve. No custom-engine runtime test passed yet.

## Milestone 71 child-frame visibility

One fresh matched visibility comparison per child type reproduced two new actions during hide and restore. Same-origin, cross-origin, and srcdoc controls all passed. Every private baseline, resumed task, and temporary cleanup passed. No keyboard event was admitted during the cycles. Aggregate Secure Input was off afterward. See [child visibility findings](child-visibility-findings.md). These are ordinary diagnostic results.

## Milestone 72 broader cache retry and content identity

The Swift-only setting did not clear WebGPU and PAL failures. The sixth build uses COMPILATION_CACHE_ENABLE_CACHING=NO, matching the passing JavaScriptCore comparison. Its active exec session is 96959. Preserve the monitor and disk reserve. The complete engine remains unverified. See [retry findings](engine-build-retry-findings.md).

The prepared InternalKeyboardControl is now engine-stable, capture-restricted, with private resume and ownership logging. Its content identity gate uses proc_pidpath. It compiles, but positive custom-engine identity is unverified. All 100 Python checks pass. The source staging regression rejects CRLF changes before mutation. A current scoped process audit found only physical browser PID 61893, no temporary research app, and aggregate Secure Input off.

## Milestone 73 page-side activity calibration

The fixture can now report focus and visibility state transitions without field text. One ordinary password comparison reported hidden state while away and visible focus transitions after return. The focus-only action reproduced. Private resume and cleanup passed. All 100 Python checks pass. See [activity findings](page-activity-findings.md). No protected custom-engine comparison ran.

A later PAL reproduction proves the quiet-log zero-exit messages are cosmetic: the target exits zero and regenerates its object. Earlier cache-failure attribution is invalid. The seventh full build is active in exec session 3890, with normal logging and upstream cache defaults. The physical browser and permissioned probes remain unchanged.

## Milestone 74 quiet-log diagnosis correction

A forced PAL Swift compile reproduced the zero-exit/no-output message in quiet mode, exited zero, and regenerated its object. The earlier cache-failure attribution is unsupported. Full attempts four through six were manually interrupted before their final exit. The confirmed configuration, Metal, and temporary-directory failures remain valid separate findings. See [log findings](engine-log-findings.md).

The seventh full build remains active in exec session 3890. It reached WebCore with normal logging and upstream caching. Its current monitor predates the new explicit status field. Read its actual exitCode and engineCompiled fields when it ends. Do not stop it because a log line contains error wording. All 102 Python checks pass. The prepared InternalKeyboardControl is currently ordinary, capture-restricted, with private resume and ownership logging.

## Milestone 75 graceful-quit controls

Readable pagehide and unload controls both terminated but recorded no action. Their candidate tests were skipped. A third readable run verified the refactored helper against a disposable control. These are inconclusive, not blocked results. The helper permits only exact disposable app paths. Its pure scope tests reject the physical identity without process access. All 102 Python checks pass. See [quit findings](quit-lifecycle-findings.md).

Automatic approval review rejected an optional live refusal test against the frozen physical browser. It did not execute. Pure tests replaced it, and no required permission question is pending. The eighth engine build is active in exec session 22023. The seventh genuinely failed because a credential API requires macOS 26.2. The eighth target matches this Mac at 26.6.

## Milestone 76 host target and source timestamps

The seventh build genuinely failed with exit code 65 on a credential API requiring macOS 26.2. The target was 26.0. The eighth build uses the host version, 26.6. Its active exec session is 22023. It currently compiles JavaScriptCore. Preserve the monitor, disk reserve, and actual exit-status evidence. See [host findings](engine-host-findings.md).

Source staging now preserves timestamps for byte-identical files. Its regression failed before the change and passed afterward. All 102 Python checks pass. This optimization does not alter the running build. The prepared InternalKeyboardControl remains ordinary, capture-restricted, with private resume and ownership logging. The frozen physical browser and probes remain unchanged.


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

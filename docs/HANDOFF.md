# Current research state

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

# AgentFreeBrowser MVP test report

Draft for publication, 2026-10-28. The current engine browser passes physical text entry, the live repeat of the focus attack, and one calibrated global input route. Matched Accessibility and scoped screenshot comparisons recover no page marker or action. Unfiltered display recording and external inspector scripting remain open acceptance tests.

## Browser and scope

The minimal macOS app includes a website address, webpage rendering, back, forward, reload, and a measured built-in keyboard route. Tabs, bookmarks, sync, extensions, and browser feature parity are outside this MVP. The current build supports US ASCII and disables mouse input. These limits are explicit usability limits.

The current executable is AgentFreeBrowserEngine, SHA-256 `12de797fbbfea6f5536b13b8ba890354170f3561f681620bb49be42f2fdf7e21`. Milestone 153 uses PID 2082 for both physical text controls and all candidate attacks. Earlier public-site and continuous-recording trials use the separate frozen preview. Their results do not transfer automatically to the new image.

The threat model covers an ordinary-user agent with available macOS grants. Root, modified browser images, kernel exploits, malicious hardware, external cameras, and the agent's separate browser are outside this PoC. The primary agent uses native computer use and the granted NativeProbe. Earlier trials also include a subagent, Playwright controls, renderer Accessibility, and ScreenCaptureKit recorders. This is a test of recorded capabilities, not every agent model.

## Current-image results

| Test | Outcome | Evidence limit |
| --- | --- | --- |
| Physical text task | User completes twice in the same process | Built-in keyboard and local fixture |
| Focus-only attack | Three cycles produce zero new actions and zero admitted input | Native-engine positive control, user-attested inactivity |
| Global key-code input | Reference completes, candidate admits no events or actions | One route and one trial |
| Host Accessibility read | Both references reveal markers, candidate does not | Bounded host tree, not renderer access |
| Accessibility action | References complete, candidate exposes no fixture controls | Fixed disposable form task |
| Window snapshot | References reveal markers, candidate returns black output | Single scoped snapshot |
| Window-inclusion display snapshot | References reveal markers, candidate has no marker | Window filter, not unfiltered capture |
| System screenshot | Candidate command fails | Inconclusive |
| Directed-window input | Reference fails, candidate skipped | Inconclusive |
| Native computer-use binding | Client times out | No browser protection inference |

The user confirms visible content and physical operation before attacks. The user repeats the physical task after the focus and observation trials. Those two human actions are the fixture's only accepted submissions. The later calibrated global input attempt records zero admitted events, 29 refusals, and no new action. Ambient events can contribute to refusal counts.

The [live findings](focus-engine-live-findings.md) and [saved evidence](evidence/focus-engine-live-results.json) preserve individual outcomes and controls. Missing frames, failed clients, and failed references do not count as protection.

## Demonstrated bypass and fix

The older frozen preview, SHA-256 `dc3ca62c174d635b9994d9bae27ff6d4dc4a7983bc36d332f720fbbfaf24df70`, has a reproducible focus-action bypass. After a human arms the fixture, external app activation causes one accepted website action in each of three cycles. No input passes the gate. The page's existing focus handler sends each request. This defeats the old image's broad action-prevention requirement.

The new browser integrates a WebKit policy that stabilizes page-visible focus and visibility while preserving native keyboard eligibility and password-input ownership. Six matched diagnostic cases cover focus, password focus, blur, visibility, and two frame types. All 18 stable cycles record no action. Every resumed typing control passes. One extra cycle after reload also records none.

Milestone 153 adds the actual human control and external focus repeat on the public executable. Its three cycles record no new action. This establishes the measured focus defense beyond diagnostic input. Physical password typing and forced renderer recovery still need tests. See [engine findings](focus-engine-browser-findings.md) and the [original bypass](preview-focus-action-findings.md).

## Earlier public-site and agent-tool trials

On the frozen preview, the user opens Google, Wikipedia search, and GitHub search. The agent and a subagent attempt native search actions. A directed key-code route works in matching readable references and leaves all three preview pages unchanged. The user confirms empty search fields afterward. GitHub also refuses externally opened HTTPS and JavaScript URLs. Other uncalibrated routes remain inconclusive. See [public-page findings](loaded-public-website-findings.md).

Earlier independent-window streaming delivers 948 complete black preview frames, with readable controls before and after. App-filtered display streaming delivers no complete candidate frame. The unfiltered recorder passes a readable reference, but the candidate coverage check refuses an overlap before pixels. See [stream findings](preview-stream-live-findings.md).

Playwright's isolated Chromium controls read pages and complete tasks. CDP and Playwright WebKit are not attachment methods for an arbitrary WKWebView. The scripted inspector client still fails its readable reference. This leaves that test uncalibrated. Appium Mac2 is untested. [Mac2 documentation](https://appium.github.io/appium-mac2-driver/latest/getting-started/)

## Capture and remaining MVP gates

The next recorder is separately pinned to the current engine image and the readable control. It retains an opaque owned backdrop, crop checks, overlap refusal, no audio or input, and a 25-second limit. Its new Screen Recording grant awaits approval. Metadata-only coverage on the earlier ungranted helper image, `82ff9c28…`, refuses an overlapping window. The final `3186515e…` image only runs its direct-refusal check. No unfiltered pixels are captured in either trial.

Apple describes `NSWindow.SharingType.none` as legacy and does not recommend it for hiding captured content. FairPlay documentation concerns streaming media, not arbitrary interactive HTML. A screenshot-file watcher also misses tools that return image bytes from memory. These facts make direct capture trials necessary. [Apple window policy](https://developer.apple.com/documentation/appkit/nswindow/sharingtype-swift.enum/none), [FairPlay Streaming](https://developer.apple.com/streaming/fps/), [computer-use integration](https://developers.openai.com/api/docs/guides/tools-computer-use-integration)

Remaining gates include unfiltered and transition capture, calibrated external inspector scripting, current-image renderer reads and keyboard observation, physical password use, recovery, and compatibility. The engine remains a workspace dependency. Hardened Runtime is off, and distribution packaging remains incomplete. The behavior classifier is offline research, not a live adaptive defense.

The report can publish the implemented browser, successful controls, measured resistance, original bypass, and validated focus fix. It cannot yet certify an agent-free MVP. The [gap audit](agent-free-gap-audit.md) tracks the remaining tests.

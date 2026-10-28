# Page activity projection with actual native focus

The next experiment changes the values WebKit sends to content processes. It keeps real AppKit window state intact. This is a research design, not an implemented protection or a general agent-free claim.

## Proposed caller usage

The research app selects its policy before constructing the web view. The configuration API below does not exist in the installed system WebKit.

```swift
let configuration = WKWebViewConfiguration()
guard ResearchActivityPolicy.configure(configuration, mode: .stableBrowsing) else {
    refuseResearchStartup()
    return
}
let webView = AXBoundaryWebView(frame: .zero, configuration: configuration)
webView.load(validatedRequest)
```

The existing hardware router and exact-object event gate remain the authority for input. They keep actual key-window and foreground-PID checks. The first activity-only experiment adds no new input token or automation bridge.

```swift
// Existing app route; pseudocode omits the source and modifier checks.
guard actualWindowIsKey && actualForegroundPID == getpid() else { return }
application.dispatchDeviceEvent(theExactLocallyAuthorizedEvent)
```

Closing the research view uses its normal native teardown. No browser-owned call balances WebKit's private Secure Event Input count.

## Data and module shape

```cpp
// Proposed engine types and signatures; not implemented yet.
enum class ContentActivityPolicy { Native, StableBrowsing };

// API::PageConfiguration copies this choice through its existing Data copy.
// A WebPageProxy captures it once for its lifetime.
const ContentActivityPolicy m_contentActivityPolicy;

OptionSet<WebCore::ActivityState> activityStateForContent() const;
```

The projection starts from the current native bit set. In stable mode it sets exactly these five flags:

- WindowIsActive
- IsFocused
- IsVisible
- IsVisibleOrOccluded
- IsInWindow

Every other flag retains its native value. There is no activity-commit API, reusable human flag, or queue of denied native transitions. DOM element focus and ordinary website JavaScript remain enabled.

`WebPageProxy::internals().activityState` stays native. Existing drawing, paint waits, throttling, process assertions, and pointer-lock cleanup keep their present source of truth. Only values crossing the content boundary use the projection.

The pinned sender audit identifies two bounded integration sites in WebPageProxy.cpp:

| Site | Proposed change |
| --- | --- |
| SetActivityState send in dispatchActivityStateChange | Send projected flags while retaining native scheduling, callbacks, and acknowledgments |
| activityState assignment in creationParameters | Seed projected flags before the new content page runs |

Immediate and queued sends converge on the first site. Provisional and remote-page creation call creationParameters. Source review must still check receivers, frame initialization, other writers, and process recovery. A two-site search alone does not prove complete coverage.

The proposed configuration setting belongs in API::PageConfiguration::Data and its Cocoa configuration adapter. Existing Data copying preserves the setting. Capture the mode in each new WebPageProxy rather than reading mutable caller state on every transition. Unknown runtime capability or ineffective readback must refuse research startup.

## Native ownership remains separate

The activity-only patch does not override isKeyWindow, isVisible, or occlusionState. It does not enable Secure Event Input for general text. Native password ownership must follow the real view, key window, responder, and foreground process.

A later ownership stage must centralize every acquisition and release in WebViewImpl. Every acquisition must reject actual ineligibility, including background editor callbacks. Return to eligibility must protect the current password field before accepted input. Cached editor state alone does not establish that ordering.

The exact editor-state barrier remains an unimplemented gate. Audit existing focused-frame, editor identifiers, and IPC ordering before adding new generations or messages. Keep preparation and final delivery in one guarded path. A delayed reply must not replay an old event or authorize a later native transition. Failed native protection must refuse sensitive delivery.

The readable password hide control reported aggregate Secure Event Input off after return. No private resumed-password ownership control established rearm timing. Do not assume existing callbacks solve this gate. Apple TN2150 also rules out treating general-text protection as a free substitute. [Apple Secure Event Input guidance](https://developer.apple.com/library/archive/technotes/tn2150/_index.html).

## Synthesis decision

The parent read all three sketches and the independent judge. Both selected Astra's separation of renderer activity from native ownership. The source audit narrows that design to outgoing projection, rather than replacing WebPageProxy's native state.

Grafts: Previous Sol's fixed policy removes the proposed authorized focus-commit interface. Sol's controls require separate actual key and foreground observations, including another app truly becoming foreground. Keep existing WebKit identities until a demonstrated stale-state path requires more state.

Rejections: constant host getters retain the measured ownership coupling. A separate offscreen host lacks a verified live interaction and independent ownership path. Timer resets cannot prevent all background reacquisition. New event wrappers must not duplicate DeviceEventGate authorization. Additional activity generations and broad surface wrappers exceed the first verified need.

The judge scored Astra 18 of 24, Sol 15, and Previous Sol 13. The latter two omitted IsVisibleOrOccluded in their written masks. These are design scores, not passing implementations. The attempted OpenCode/DeepSeek review failed before execution because its configured key expired. An independent Codex reviewer completed the comparison. Model-family diversity is reduced.

## Verification and first implementation

1. Inventory every sender, receiver, creation path, and secure owner call in the pinned source. Preserve hashes and source revision.
2. Implement only the immutable configuration choice and outgoing five-flag projection. Check all bit combinations for native identity, stable flags, nonprotected-flag preservation, and idempotence.
3. Validate the patch against the exact source. Establish a bounded build and disk plan before fetching a full engine. Do not call patch application a successful engine build.
4. Build and launch only a separate research app. Verify loaded framework paths and build identities in both UI and replacement content processes.
5. Repeat matched focus, blur, visibility, password, frame, navigation, occlusion, and recovery tests. Add child-frame lifecycle listeners; the existing frame matrix measures entry only.
6. Instrument WebKit's own secure flag and native API return values. Test actual foreground transfer and background editor changes. Aggregate system state corroborates ownership but does not identify its owner.
7. Complete ordinary text, password rearm, visible redraw, selection, scrolling, and cleanup controls. Private input establishes routing only. Physical controls remain necessary before usability claims.

The host has Xcode 27.1, Metal, 32 GiB memory, 10 logical CPUs, and about 204 GiB free. This confirms read-only prerequisites. Source compatibility, peak build size, signing, and custom-framework loading remain untested. Use scoped build and launch settings; keep the frozen physical browser and approved probes unchanged. [WebKit build options](https://docs.webkit.org/Build%20%26%20Debug/BuildOptions.html), [WebKit prerequisites](https://webkit.org/build-tools/).

The original MVP avoided a custom engine. The measured coupling justifies an isolated engine experiment within the user's continued research request. It does not commit the product to distributing a fork. The fixed activity policy also changes hidden-page semantics and may increase background work. Measure those costs.

This boundary covers the demonstrated activity route. Other native state, geometry, inspection, capture, session, and source-trust routes remain separate tests. No finite fixture result establishes every website as agent-free.

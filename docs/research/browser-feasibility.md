# Minimal macOS browser feasibility research

Research date: 2026-10-23. Sources are official documentation, first-party source code, or vendor engineering guidance. This report includes no local browser experiments. Recommendations are judgments, not measured results.

## Decision for the proof of concept

A minimal browser can remove the interfaces that agents commonly use. It cannot promise that all software running as its user cannot read or control it.

The scope is macOS only, with arbitrary websites and web apps. There is no site-owner integration or managed-device requirement.

Start with Swift, AppKit, and WKWebView. Disable inspection and expose no automation bridge. Test accessibility and synthetic input before building browser features. Treat screenshot protection as unproven and likely incomplete on current macOS.

Rejecting agent control remains worth testing even if screenshots reveal content. A successful input defense supports a narrower control-blocking claim. It cannot establish that agents cannot read the page.

Use the promise: "Blocks the tested agent interfaces on the supported build." Do not use "agent-proof browser." If either screen reading or control succeeds, do not make a broad agent-free claim.

## Threat boundary

Test agents with granted Accessibility and Screen Recording permissions. These grants belong to the agreed threat model, not an excluded privileged scenario.

Keep separate results for four agent capabilities:

1. Browser automation through a debugging protocol, extension, scripting interface, or application bridge.
2. Desktop automation through accessibility APIs and synthetic keyboard or mouse input.
3. Screen reading through screenshots and optical character recognition.
4. Local code execution with the user's file access, environment control, process launch, or stronger privileges.

Chromium excludes attacks by software running with the user's account privileges from its normal security model. It also excludes compromised operating systems. A new browser needs an explicit, narrower claim for this threat. [Chromium security FAQ](https://chromium.googlesource.com/chromium/src/+/main/docs/security/faq.md)

This does not mean all same-user processes can freely inspect a hardened macOS process. Apple documents debugger and injected-library protections. These controls reduce specific attacks. They do not establish that a browser can defeat every program the user can run. [Apple hardened-runtime explanation](https://developer.apple.com/videos/play/wwdc2019/703/)

Product implication, inferred from these boundaries: protection against ordinary agent tools is a useful PoC. Protection against an unrestricted hostile local account needs operating-system isolation, managed privileges, or a separate device.

## Browser engine choices

| Choice | Documented controls | PoC judgment and unresolved work |
| --- | --- | --- |
| Swift, AppKit, WKWebView | `isInspectable` defaults to false. WebKit supports separate website data stores. | Best initial macOS choice. Fewer application-provided automation features to remove. Accessibility and input restrictions still need experiments. |
| Electron | Chromium sandbox and context isolation. Packaging fuses disable selected Node execution and debugger features. | Convenient prototype tooling, but more configuration and release checks. A disabled DevTools menu does not prove remote debugging is absent. |
| Native CEF host | CEF documents disabling command-line processing and configuring remote debugging. | Credible Chromium option when compatibility is decisive. More integration and update work. Do not fork Chromium for the first experiment. |

The first row uses [Apple inspection documentation](https://developer.apple.com/documentation/safari-developer-tools/enabling-inspecting-content-in-your-apps) and [WebKit profile documentation](https://webkit.org/blog/14423/building-profiles-with-new-webkit-api/). The Electron controls come from [Electron security guidance](https://www.electronjs.org/docs/latest/tutorial/security) and [Electron fuses](https://github.com/electron/electron/blob/main/docs/tutorial/fuses.md). CEF controls appear in its [official usage guide](https://github.com/chromiumembedded/cef/blob/master/docs/general_usage.md).

Engine security updates remain required. Chromium warns that downstream browsers need current security fixes. [Chromium guidance for browser vendors](https://chromium.googlesource.com/chromium/src/+/main/docs/security/faq.md)

## Debugging and DOM access

Apple introduced the public inspectability property for macOS 13.3. Set `isInspectable = false` explicitly on every WKWebView. Apple says disabling it closes an active Safari Web Inspector session and stops further inspector information. Older SDK-linked debug builds have different behavior. Test the packaged release artifact. [Apple inspection documentation](https://developer.apple.com/documentation/safari-developer-tools/enabling-inspecting-content-in-your-apps)

This blocks the documented inspector route. It does not remove the document object model, or DOM, from the engine. Web apps still require their own JavaScript and DOM. Do not expose application methods that evaluate scripts, return page contents, or export cookies to outside callers.

The Chrome DevTools Protocol, or CDP, exposes browser inspection commands. Its accessibility domain can return complete trees and query nodes that accessibility normally ignores. Hiding page elements from assistive technology does not protect them from an exposed CDP endpoint. [CDP overview](https://chromedevtools.github.io/devtools-protocol/) and [CDP accessibility commands](https://chromedevtools.github.io/devtools-protocol/tot/Accessibility/)

Electron supports Chromium remote debugging and a separate Node inspector. Packaging fuses disable Node options, Node inspector arguments, and `ELECTRON_RUN_AS_NODE`. The Node inspector fuse documentation does not promise to disable every Chromium debugging entry point. Test both separately. [Electron command-line switches](https://www.electronjs.org/docs/latest/api/command-line-switches) and [Electron fuses](https://github.com/electron/electron/blob/main/docs/tutorial/fuses.md)

CEF documents `command_line_args_disabled` and `remote_debugging_port`. These offer explicit host controls. Their presence does not prove the final build blocks every debugger path. Test the pinned CEF version with hostile launch arguments. [CEF usage guide](https://github.com/chromiumembedded/cef/blob/master/docs/general_usage.md)

## Accessibility extraction and control

macOS accessibility exposes a hierarchy of elements. AppKit automatically populates child relationships for accessible descendants. Marking a containing view as inaccessible is insufficient evidence that its descendants cannot appear. [AppKit accessibility children](https://developer.apple.com/documentation/appkit/nsaccessibility-c.protocol/accessibilitychildren)

Chromium documents external tree-inspection tools and the macOS accessibility API. Accessibility normally activates on demand. Its `--disable-renderer-accessibility` switch disables renderer accessibility. Electron also exposes accessibility controls. None establishes that one runtime call permanently defeats every external request. [Chromium accessibility documentation](https://github.com/chromium/chromium/blob/main/docs/accessibility/overview.md) and [Electron accessibility controls](https://www.electronjs.org/docs/latest/api/app)

Disabling the same tree that agents read also removes information that screen readers need. Apple describes this information as the basis for assistive technologies to understand and interact with apps. [Apple accessibility session](https://developer.apple.com/videos/play/wwdc2025/229/)

AppKit supports `isAccessibilitySelectorAllowed(_:)` to refuse specified accessibility selectors on an element. Its contract does not identify the caller as human or agent. [Apple selector access documentation](https://developer.apple.com/documentation/appkit/nsaccessibilityprotocol/isaccessibilityselectorallowed(_:))

Unknown: these public AppKit controls may not suppress every WKWebView descendant in separate WebKit processes. Test navigation, iframes, new windows, focus changes, and browser process restarts. Do not assume that overriding one host view covers arbitrary web content.

Decision: preserve VoiceOver access to browser controls and web content for general usage. If a protection removes that access, report that the browser lacks general-usage readiness. A research-only mode may demonstrate the tradeoff, but it cannot satisfy this requirement. No reviewed source establishes a public API that gives ordinary assistive tools full access while refusing every agent.

## Screenshot protection

Apple now calls `NSWindow.SharingType.none` a legacy constant that macOS no longer uses. Electron explicitly says newer applications using ScreenCaptureKit can capture windows despite `setContentProtection(true)`. [Apple window-sharing constants](https://developer.apple.com/documentation/appkit/nswindow/sharingtype-swift.enum) and [Electron content-protection documentation](https://www.electronjs.org/docs/latest/api/browser-window#winsetcontentprotectionenable-macos-windows)

These sources establish an incomplete protection mechanism. They do not establish one exact macOS version boundary for every capture program. Do not turn an old successful `screencapture` test into a claim about ScreenCaptureKit, recording applications, or all macOS 15 and later builds. An Apple forum report also describes capture results changing after filter refresh. Apple requested a reproducible bug report. [Apple engineering forum response](https://developer.apple.com/forums/thread/808016)

Windows supports `SetWindowDisplayAffinity` with `WDA_EXCLUDEFROMCAPTURE` from Windows 10 version 2004. It applies to a top-level window owned by the calling process and requires desktop composition. Microsoft limits protection to a specific set of public capture features. It explicitly gives no strict content-security guarantee. [Microsoft display-affinity API](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwindowdisplayaffinity)

Recommendation: a current macOS browser cannot claim universal screenshot blocking based on these public controls. Windows is outside this MVP. Its capture API is an excluded comparison, not a fallback platform. External cameras, privileged capture, and untested capture programs remain outside any demonstrated result.

## Synthetic input

Core Graphics exposes the source Unix process ID and source-state ID for events. Apple defines source-state IDs as event-state tables. Programs can create sources with combined-session, HID-system, or private state. A HID state ID alone is therefore not a documented proof of physical input. [Event process ID](https://developer.apple.com/documentation/coregraphics/cgeventfield/eventsourceunixprocessid), [event state ID](https://developer.apple.com/documentation/coregraphics/cgeventfield/eventsourcestateid), and [event source states](https://developer.apple.com/documentation/coregraphics/cgeventsourcestateid)

Core Graphics also exposes event creation, posting, source assignment, and integer-field setters. The reviewed documentation does not promise that source metadata is an unforgeable hardware attestation. Treat rejection rules as tested heuristics. [CGEvent API](https://developer.apple.com/documentation/coregraphics/cgevent)

The DOM standard defines `isTrusted` through event dispatch by the user agent. It does not attest physical human input. A JavaScript event check cannot substitute for native input tests. [DOM event trust definition](https://dom.spec.whatwg.org/#dom-event-istrusted)

Test native input rejection independently from screen reading. Cover CGEvent posting, AppleScript through System Events, AX actions and value setters, and events with changed source fields. Instrument only the test fixture. Do not require production websites to implement these checks.

Test input methods used by real people. Include input methods for other languages, dictation, keyboard remapping, password-manager insertion, and accessibility tools. A physical-input-only policy can reject these legitimate paths.

## Profiles and session files

WKWebsiteDataStore manages cookies and website storage. Its default store persists data. A nonpersistent store keeps website data in memory. Named persistent stores support separate profiles from macOS 14. [Apple data-store API](https://developer.apple.com/documentation/webkit/wkwebsitedatastore) and [WebKit profile documentation](https://webkit.org/blog/14423/building-profiles-with-new-webkit-api/)

For the PoC, use a fresh profile and synthetic test accounts. Do not import Safari or Chrome cookies. An ephemeral profile reduces stored session files but requires users to log in again. Separate profiles prevent accidental session sharing. They do not prove resistance to hostile same-user code.

## Experiments that decide feasibility

Run each attack against an ordinary browser as a positive control. Record the exact OS build, engine version, packaged-app hash, tool version, permissions, steps, and raw result. No experiment below ran during this research.

| Experiment | Pass condition | Failure means |
| --- | --- | --- |
| Inspector attachment | Safari inspector or Chromium tooling cannot discover or attach to protected content. | The documented browser-automation route remains open. |
| Relaunch with debugging overrides | Command-line and environment overrides expose no usable debugger after relaunch. | Disabling the DevTools UI is cosmetic. |
| Accessibility read | External macOS AX tools recover none of the unique test document text, form values, or actions. | The agent can still read or operate through accessibility. |
| Accessibility usability | A VoiceOver user completes browser navigation and the agreed web-content tasks. | The browser lacks general-usage readiness. |
| macOS capture | ScreenCaptureKit display and window capture reveal none of the test text after start, resize, and filter changes. | Screenshot resistance fails for that route. Legacy capture results cannot override this failure. |
| Synthetic input | Each named automation route cannot change a field or submit a form. Hardware controls still work. | The route remains usable even if the agent cannot read the page. |
| Alternative output | Copy, print, save, drag, notifications, and native dialogs reveal no protected test text through permitted automation. | The agent has another export path. |
| Session isolation | A clean normal browser cannot reuse the protected test session. The chosen persistence policy matches restart behavior. | Session sharing or persistence violates the requirement. |
| Release hardening | The packaged macOS app denies ordinary debugger attachment and contains no development inspection entitlement. | Development behavior invalidates release claims. |

Use a fixed document with unique fake secrets and a harmless submission counter. Readability and action success are separate scores. Do not count a tool error as a defense unless the positive control succeeds.

## Decisions and remaining experiments

The scope includes agents with granted Accessibility and Screen Recording permissions. Measure screen reading and control separately. Both must fail before any broad agent-free claim. Preserve VoiceOver for general usage, or report a research-only result.

The remaining questions require experiments:

- Can a WKWebView public implementation hide the full web accessibility tree across process changes and popups?
- If WKWebView fails a required test, does a Chromium host improve that result enough to justify its integration cost?
- Which real web apps and login flows must work inside the chosen engine?
- Which macOS capture APIs and versions must the release test?

Resolve these questions before investing in tabs, bookmarks, or browser customization. A successful control experiment remains useful research when screen reading succeeds. It does not satisfy the broader protection claim.

# Keyboard observation boundary

Research date: 2026-10-25. This review uses Apple documentation, the installed SDK, and WebKit source. It installs no monitor and runs no attack.

## Physical use leaves an observation question

The root agent reports one accepted physical task on the current restricted browser. Its matched external input trials admit no additional action. Those results test action delivery. They do not test whether a second process can observe the person's physical keys.

The keyboard router reconstructs private application events from a selected HID device. Its event gate rejects ambient events in `sendEvent`. That check controls what the browser dispatches. It does not document a way to remove the physical keys from earlier OS observation paths. This is an inference from the router and public event architecture, not a measured disclosure. [Current router](../../Sources/Browser/DeviceKeyboard.swift), [Apple event architecture](https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/EventOverview/EventArchitecture/EventArchitecture.html)

## Accessibility and Input Monitoring are different permissions

Apple's WWDC19 explanation distinguishes two Quartz tap options. A `listenOnly` tap requires Input Monitoring authorization. A `defaultTap` tap requires Accessibility authorization because its callback can influence delivery. The latter callback can also return the original event unchanged. Its ability to observe does not depend on actually changing an event. [Apple WWDC19, 35:32](https://developer.apple.com/videos/play/wwdc2019/701/?time=2132), [Apple tap options](https://developer.apple.com/documentation/coregraphics/cgeventtapoptions)

Thus, the threat model's Accessibility grant already includes an observation-capable active-tap route in Apple's explanation. This research does not install that route. The desktop incident makes an active tap unsuitable for an exploratory test on this Mac.

Do not infer that Accessibility automatically equals a separate Input Monitoring grant. Screen Recording permission also does not establish keyboard-listening permission. A passive tap must report its own effective authorization and creation result.

`CGPreflightListenEventAccess` checks existing listening access without a request. The installed `CGEvent.h` separately declares preflight and request functions for listening and posting. `IOHIDCheckAccess` likewise distinguishes listening from posting. Its listening request applies to `IOHIDManager` and `IOHIDDevice`. [Apple WWDC19 keyboard authorization](https://developer.apple.com/videos/play/wwdc2019/701/?time=1203), [Apple HID status API](https://developer.apple.com/documentation/iokit/3181573-iohidcheckaccess)

An absent passive-tap grant does not prove protection against every Accessibility-authorized observer. Conversely, an observer with an additional Input Monitoring grant tests an expanded permission case. Its result must retain that qualifier.

## A passive AppKit route deserves a control

Apple documents `NSEvent.addGlobalMonitorForEvents` as a receiver of copies of events sent to other apps. The callback cannot change or prevent delivery. The same page says key monitoring requires enabled accessibility or an application trusted for Accessibility. This supplies a concrete read-only observation route within the stated permission model. [Apple global monitor API](https://developer.apple.com/documentation/appkit/nsevent/addglobalmonitorforevents(matching:handler:))

The current API page retains historical OS X details. Apple's 2026 DTS answer separately recommends the modern Input Monitoring tap path for sandboxed apps. That answer does not establish that an unsandboxed Accessibility-authorized global monitor fails on this OS. These sources justify a runtime control, not a universal permission-equivalence rule. [Apple DTS explanation](https://developer.apple.com/forums/thread/811443)

The returned monitor object alone proves no key disclosure. An observer must actually receive the controlled physical sequence. Missing events also require a successful ordinary-text reference before they count as a refusal.

The existing NativeProbe has effective Accessibility and Screen Recording grants. Its permission record does not establish its separate listening grant. A new observer binary changes code identity and cannot silently inherit those effective grants. [Code identity findings](tcc-code-identity.md)

## WKWebView protects password focus in published source

WebKit's macOS `WebViewImpl::updateSecureInputState` checks whether its window is key and the view has focus. When the editor reports a password field, it calls `EnableSecureEventInput`. It disables that state for ordinary fields, loss of focus, and reset. [WebKit macOS implementation, lines 2694-2725](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/mac/WebViewImpl.mm#L2694)

This source supports automatic secure input during normal focused password entry. It does not prove that the installed framework matches current WebKit `main`, or that every focus transition works in this custom browser. The candidate needs a password-field control on its actual build.

Apple's TN2150 describes Secure Event Input as protection against keyboard intercept processes, including event taps. It also names legacy key-state observation. The note directs apps to limit secure input to private entry fields and disable it when ordinary text or background focus resumes. The note is archived. [Apple TN2150](https://developer.apple.com/library/archive/technotes/tn2150/_index.html)

Password focus therefore cannot supply protection for the browser's address field, search boxes, messages, or ordinary form text. The current native address field is an `NSTextField`, not an `NSSecureTextField`. The source-policy gate does not change that. [Current browser sources](../../Sources/Browser/DeviceKeyboard.swift)

App-lifetime Secure Event Input is outside this design and the proposed experiments. A global suppression rule would affect other applications and their legitimate input tools.

## Smallest bounded observation experiment

The next observation test can use the passive AppKit API without a modifying tap. It still needs a genuine physical control.

1. Freeze the observer's signed artifact and record its effective Accessibility and listening status without requesting a grant.
2. Limit the observer to the exact research browser's foreground PID and a short timer.
3. Test a fresh fake phrase in an ordinary field, then a password field, with independent fixture completion evidence.
4. Save only expected-phrase match status, event counts, field category, authorization results, and cleanup status.
5. Stop the observer on focus loss, timeout, or unexpected application ownership.

The process must discard unrelated events before text extraction and omit all raw key codes and text from saved artifacts. A successful match supports only the measured fake phrase, observer identity, permissions, field, and OS build.

A separate Quartz control can use `listenOnly` only when its existing authorization allows it. The PID-specific tap API can restrict the requested target. Tap creation can return null or remove unauthorized event types from the requested mask. Missing keys are inconclusive without calibration. [Apple tap creation API](https://developer.apple.com/documentation/coregraphics/cgevent/tapcreate(tap:place:options:eventsofinterest:callback:userinfo:))

No new permission request follows from this plan. An inaccessible API remains untested in the current permission case. An agent-generated phrase cannot replace the physical-key control.

## Claim allowed by the evidence

There is a documented observation route that the current browser trials did not measure. There is also source evidence for password-specific protection. No reviewed public contract gives ordinary WKWebView text the same automatic protection.

Blocking ambient input and hiding captured pixels do not establish confidentiality of physical keystrokes. A successful observation would reject that confidentiality claim even if the observer completes no website action. Until the matched observation test exists, the result remains an open boundary.


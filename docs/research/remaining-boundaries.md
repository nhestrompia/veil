# Remaining macOS boundaries

Research date: 2026-10-23. This report uses Apple documentation, Apple source code, and the installed macOS 27 SDK. No experiment ran during this research.

## Two mechanisms still justify experiments

The best remaining capture experiment uses `AVSampleBufferDisplayLayer.preventsCapture` with application-generated pixels. The best remaining input experiment compares application events with independent reports from an identified HID device. HID means Human Interface Device.

Neither mechanism establishes an agent-free browser. Capture exclusion leaves accessibility and blind input open. Device reports establish device activity, while the browser still needs to protect the connection between that activity and the intended action.

These experiments retain the agreed threat model. The attacker can use the same account with Accessibility and Screen Recording permission. Root, kernel changes, modified browser binaries, and external cameras remain outside the scope.

## Public capture protection accepts a useful test

Apple describes `AVSampleBufferDisplayLayer` as a layer for compressed or uncompressed video frames. Its public `preventsCapture` property marks image data for protection against capture. The installed header declares this property available since macOS 10.15. These contracts justify an arbitrary-pixel experiment without FairPlay content or an encrypted overlay. They do not promise protection against every capture method. [Apple display-layer API](https://developer.apple.com/documentation/avfoundation/avsamplebufferdisplaylayer), [Apple capture-protection property](https://developer.apple.com/documentation/avfoundation/avsamplebufferdisplaylayer/preventscapture)

The current SDK also documents `CMSampleBuffer` objects that wrap `CVPixelBuffer` objects. Its header requires IOSurface-backed pixel buffers for this route. `kCVPixelBufferIOSurfacePropertiesKey` with an empty dictionary requests that backing. Apple exposes `sampleBufferRenderer` for enqueue operations. The old layer enqueue method is deprecated from macOS 15. [Apple video renderer](https://developer.apple.com/documentation/avfoundation/avsamplebuffervideorenderer)

The smallest useful producer draws fresh text into a pixel buffer. A second stage replaces that producer with actual HTML snapshots. A clear snapshot inside the protected process is part of this design. It must never appear in another visible window or an external export interface. A local snapshot does not by itself prove that an outside process can read process memory.

The experiment needs a matched unprotected layer, fresh markers, and independent capture clients. It also needs an observation that the person can see the protected content. A black capture from a failed renderer proves nothing. Capture checks must cover window and display capture, stream capture, system screenshots, resize, fullscreen, and changed filters.

`preventsCapture` protects the layer's content. It does not promise to protect an underlying WKWebView, a popup, a menu, a tooltip, or accessibility text. An overlay above readable HTML is therefore insufficient. A successful display-layer result would justify an interactive HTML producer and a check of every secondary window. It would not yet justify a browser-engine fork.

## Secure Event Input is an interception defense

Apple introduced `EnableSecureEventInput` to stop other processes from intercepting keyboard input. Apple directs applications to enable it for sensitive fields and disable it after those fields lose focus. The technical note explicitly rejects general text use and application-lifetime use. The note does not claim to authenticate input origin or reject injected mouse and keyboard events. [Apple technical note TN2150](https://developer.apple.com/library/archive/technotes/tn2150/_index.html)

A small sensitive-field experiment could test CGEvent injection while secure input is active. Its result would apply to that field and OS build. Continuous secure input is a poor foundation for general browsing under Apple's documented usage rules. It also gives no documented protection for pointer actions or accessibility setters.

## Device reports are stronger evidence than CGEvent metadata

`IOHIDManager` can discover devices and receive their input reports or parsed input values. `IOHIDValueGetTimeStamp` returns OS absolute time. A device callback therefore offers a second observation independent of the source fields on an application event. The APIs do not document a cryptographic claim that the device or its operator is human. [Apple manager API](https://developer.apple.com/documentation/iokit/iohidmanager_h), [Apple value API](https://developer.apple.com/documentation/iokit/iohidvalue_h)

The modern `CoreHID` framework offers `HIDDeviceManager` and `HIDDeviceClient`. The installed Swift interface marks these APIs available from macOS 15. A client can monitor raw input reports with timestamps and parsed element updates. Apple's guide says some devices, including keyboards, require user approval. The existing probe's posting permission does not establish Input Monitoring permission. [Apple HID communication guide](https://developer.apple.com/documentation/CoreHID/CommunicatingWithHIDDevices), [Apple notification method](https://developer.apple.com/documentation/corehid/hiddeviceclient/monitornotifications(reportidstomonitor:elementstomonitor:))

The strongest initial test records event types, device identifiers, timestamps, and relevant button or movement values while the research window has focus. Keyboard content should remain absent from saved logs. The test compares physical activity with the existing session, HID-state, private-state, and curved CGEvent adapters. It requires real physical input as a positive control. Computer-use tools supply synthetic input and cannot stand in for that control.

A rule that accepts any event shortly after device activity is weak. The proposed stronger rule matches each action against a particular unused report. It must match the button or key identity and account for duplicate delivery, ordering, coalescing, and key repeat. Pointer movement needs a defined mapping between device movement and browser coordinates. Matching time alone does not establish that mapping.

An active Quartz event tap can change an event, replace it, or delete it. This creates an adaptive attack against simple report correlation. An attacker can change the location of a physical click while its hardware button report still exists. Whether the complete attack works against a particular implementation requires a test. [Apple event-tap callback contract](https://developer.apple.com/documentation/coregraphics/cgeventtapcallback)

A separate browser path that derives actions from device reports and refuses ambient application events is a stronger hypothesis. It needs its own pointer state and complete input routing. Accessibility actions must not bypass that route. Text composition, dictation, remapping, and assistive input remain usability questions. No reviewed source establishes a public API that supplies those features while proving human intent.

## Virtual HID requires a separate attacker check

`CoreHID.HIDVirtualDevice` can create a software peripheral and dispatch input reports. Apple explains that the system treats such a peripheral as an external device. The current SDK exposes this API from macOS 15. Virtual devices can specify product, vendor, transport, and other descriptive properties. Those names alone are unsuitable as hardware authentication. [Apple virtual-device guide](https://developer.apple.com/documentation/corehid/creatingvirtualdevices)

Apple's open-source `IOHIDResourceDeviceUserClient::initWithTask` checks `com.apple.developer.hid.virtual.device` or the private `com.apple.hid.manager.user-access-device` entitlement. A process without either entitlement fails that published check. Apple also documents the developer entitlement. This is evidence for an entitlement boundary in that source revision. It is not a measured result on this machine or proof that every virtual input route needs that entitlement. [Apple entitlement](https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.developer.hid.virtual.device), [Apple user-client source](https://github.com/apple-oss-distributions/IOHIDFamily/blob/main/IOHIDFamily/IOHIDResourceUserClient.cpp)

The useful attack control creates a virtual keyboard without that entitlement, records the result, and exits without dispatching global input. Existing Accessibility permission does not itself establish virtual-device permission. Root access and driver installation are unnecessary for this refusal test. A refusal must remain specific to the API, signature, entitlements, and OS build.

`IOHIDDeviceSetReport` sends reports to a device. Apple limits this API to output or feature reports. It is not documented as a way to inject an input report into a physical keyboard. `IOHIDPostEvent` is a separate, deprecated API. The installed header says posting requires user approval. That route deserves an attack check because permissioned posting belongs to the threat model. Its presence does not establish that posted events produce raw device reports. [Apple report API](https://developer.apple.com/documentation/iokit/1588656-iohiddevicesetreport), [Apple post-event API](https://developer.apple.com/documentation/iokit/1555406-iohidpostevent)

## Ranked experiments and stop conditions

1. **Protected arbitrary pixels, then HTML.** Compare protected and unprotected layers with identical fresh content. Continue only after real visible output and matched capture controls work. Stop the candidate if a supported capture route reads the protected content.
2. **Raw device observations.** Compare physical input and each synthetic adapter without a blocking rule. Continue only if the browser receives useful physical reports and the observations separate the tested injections. Missing grants or unsupported hardware are inconclusive.
3. **Adaptive input attacks.** Test unused-report matching, altered physical events, replay, pointer redirection, accessibility setters, and `IOHIDPostEvent`. Test unentitled virtual-device creation separately. Any completed action rejects the broad input-blocking claim.
4. **Input routing from device reports.** Consider this larger change only if the observation experiment succeeds. Ignore ambient application events in this build. Require people to complete navigation, text entry, scroll, and focus tasks before treating rejected automation as useful protection.

Human usability and agent resistance require separate evidence. A browser that ignores every event blocks agents but also blocks people. No candidate meets the agent-free goal until both evidence sets exist.

## Local SDK evidence

The SDK root came from `xcrun --show-sdk-path`. Relevant files are `AVFoundation.framework/Headers/AVSampleBufferDisplayLayer.h`, `IOKit.framework/Headers/hidsystem/IOHIDLib.h`, `IOKit.framework/Headers/hid/IOHIDValue.h`, and `CoreHID.framework/Modules/CoreHID.swiftmodule/arm64e-apple-macos.swiftinterface`. These paths are under `System/Library/Frameworks` in the SDK. Header facts above describe this installed SDK, while runtime results still require the packaged experiments.

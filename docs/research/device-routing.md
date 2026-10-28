# Input routing from selected devices

Research date: 2026-10-23. Sources are public Apple documentation, Apple HID source, the installed macOS 27 SDK, and the project's saved results. This report collects no input and runs no new attack.

## Test a separate input path

The next useful experiment generates application events from reports received from one selected device. It rejects ambient mouse and keyboard events, including events posted with HID source metadata. It does not open a time window after physical activity during which arbitrary events become acceptable.

The smallest falsifiable version supports a pointer and one ordinary HTML button. It needs no keyboard translation, browser features, or production website changes. A person must activate that button through the selected device. The existing agents must fail to activate the same button on the same build. Until both results exist, a rejected synthetic action can reflect a broken input path.

The current stricter accessibility overrides omit the page from the tested accessibility reads, but known-layout CGEvent input still completes the task. That finding makes input routing independent work. Hiding the tree does not establish input prevention.

## Device reports do not attest human intent

`IOHIDManager` can discover devices and receive reports or parsed input values. `IOHIDValueGetTimeStamp` returns OS absolute time. These observations occur through a different interface than ordinary AppKit events. They do not cryptographically attest a physical device or a person's intended action. [Apple manager API](https://developer.apple.com/documentation/iokit/iohidmanager_h), [Apple value API](https://developer.apple.com/documentation/iokit/iohidvalue_h)

The routing candidate must bind to a particular observed device object or service for the current process lifetime. Matching every keyboard and mouse is insufficient. Product names, vendor identifiers, transport strings, and element flags are descriptive inputs. The reviewed APIs do not document them as hardware authentication.

`IOHIDElementIsVirtual` describes whether an element is virtual. Its contract does not identify every software-created device or establish human origin. Treating this flag alone as an attestation would repeat the earlier source-state mistake. [Apple virtual-element API](https://developer.apple.com/documentation/iokit/1564125-iohidelementisvirtual)

Device removal must invalidate the binding and pending actions. A new device must not silently inherit permission because its descriptive fields match. A minimal build can support one named hardware configuration while the experiment tests these assumptions. That limit must remain visible in the results.

## A concrete synthesis path can produce HID reports

The installed `IOKit.framework/Headers/hidsystem/IOHIDLib.h` declares the deprecated `IOHIDPostEvent` API. Its options include `kIOHIDPostHIDManagerEvent`, with value `0x8`. The same header documents user approval for posting through `IOHIDPostEvent`. Posting permission and device-listening permission are separate request types. [Apple posting API](https://developer.apple.com/documentation/iokit/1555406-iohidpostevent)

Apple's `IOHIDSystem::extPostEventGated` source checks permission through `mac_iokit_check_hid_control` for non-null events. With `kIOHIDPostHIDManagerEvent`, it creates a pointing-device or keyboard-device object and calls its posting methods. The source does not require creation of an `IOHIDUserDevice` for this route. Runtime availability and permission behavior still need measurement on this machine. [Apple system source](https://github.com/apple-oss-distributions/IOHIDFamily/blob/main/IOHIDSystem/IOHIDSystem.cpp)

`IOHIDPointingDevice::postMouseEvent` writes report data and calls `handleReport`. `IOHIDKeyboardDevice::postKeyboardEvent` converts the key code, updates its report, and also calls `handleReport`. These implementations supply a concrete reason to reject the rule that any HID callback proves physical input. The system posting code currently passes zero button state to its pointing path, so movement, scrolling, and keyboard reports merit separate controls. [Apple pointing-device source](https://github.com/apple-oss-distributions/IOHIDFamily/blob/main/IOHIDSystem/IOHIDPointingDevice.cpp), [Apple keyboard-device source](https://github.com/apple-oss-distributions/IOHIDFamily/blob/main/IOHIDSystem/IOHIDKeyboardDevice.cpp)

The separate virtual-device route requires its own assessment. Apple source checks `com.apple.developer.hid.virtual.device` or a private entitlement before opening the relevant user client. CoreHID also exposes software peripherals through `HIDVirtualDevice`. [Apple user-client check](https://github.com/apple-oss-distributions/IOHIDFamily/blob/main/IOHIDFamily/IOHIDResourceUserClient.cpp), [Apple virtual-device guide](https://developer.apple.com/documentation/corehid/creatingvirtualdevices)

The [saved creation check](../evidence/virtual-device-results.json) returns no device for either tested creation API in three trials. The executable had no entitlements, sent no reports, and had no entitled positive control. This is a bounded creation result. It does not prove that permissioned agents cannot produce HID reports through the system-posting path.

`IOHIDDeviceSetReport` is not a documented input-injection substitute. Apple limits that method to output or feature reports sent to the device. Attempts to change device properties, existing remapping tools, and an already installed virtual driver remain distinct questions. They must not inherit a prevention result from the creation-only check. [Apple device-report API](https://developer.apple.com/documentation/iokit/1588656-iohiddevicesetreport)

## AppKit offers event creation and normal dispatch

`NSEvent.mouseEvent` creates mouse events with a location in the target window's coordinates. `NSEvent.keyEvent` creates key events with characters and a virtual key code. A selected-device callback can therefore create a fresh application event without posting a global CGEvent. [Apple event API](https://developer.apple.com/documentation/appkit/nsevent)

Apple documents `NSApplication.postEvent` as the queue insertion method and `NSApplication.sendEvent` as normal event dispatch. `NSApplication.sendEvent` is overridable. In contrast, the `NSWindow.sendEvent` documentation explicitly says never to invoke it directly. A public-API experiment should retain normal application dispatch instead of invoking a window's dispatcher as its new input interface. [Apple application dispatcher](https://developer.apple.com/documentation/appkit/nsapplication/sendevent(_:)), [Apple window dispatcher](https://developer.apple.com/documentation/appkit/nswindow/sendevent(_:))

The proposed distinction is process-private object identity. The device callback creates an event and records that exact object as eligible for one dispatch. The application rejects ambient mouse and keyboard events that lack that record. Timestamp, source PID, source state, user-data fields, and trajectory shape must not grant eligibility. A broad Boolean that accepts events during a nested dispatch is also unsuitable.

This design is an implementation hypothesis. The experiment must test whether queue insertion and dispatch preserve the event object's identity. It must also test local monitors, modal tracking, menus, dragging, and nested event loops. A single application override does not prove that every AppKit path applies the same check. Apple describes modal event tracking and separate responder actions. [Apple event architecture](https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/EventOverview/EventArchitecture/EventArchitecture.html)

The HTML button must receive the normal WebKit input path. A native callback that directly changes page JavaScript or the server counter would test a different mechanism. Public AppKit event APIs do not guarantee that reconstructed input supports every WKWebView interaction. Real task completion supplies that evidence.

## Pointer state must remain independent

The experiment needs its own visible pointer inside the content area. Its position starts at a fixed point and changes only from the bound device's accepted movement reports. It must not use `NSEvent.mouseLocation`, CGEvent locations, posted deltas, or global button state to choose the action target.

Otherwise, an attacker can move the system cursor and let a later physical click select the attacker's target. Using a real click as permission for a synthetic position would recreate the correlation problem.

`IOHIDElementIsRelative` distinguishes movement deltas from absolute coordinates. Relative elements require integration into the private pointer position. Absolute elements require normalization through the element's declared range. Units, acceleration, scale, clamping, and button transitions need explicit behavior. [Apple relative-element API](https://developer.apple.com/documentation/iokit/1564129-iohidelementisrelative)

A trackpad may not supply the same relative mouse reports as a particular external mouse. Rejecting system shim devices may remove reports that a hardware configuration normally uses. The physical baseline must establish which accepted source actually carries movement. No existing synthetic trace resolves this question.

## Keyboard support is a later experiment

HID usage codes are not AppKit virtual key codes. A direct cast does not translate them. The prototype would need a documented mapping, device modifier state, key-up behavior, repeat state, and text input handling. Raw key codes and text can remain transient in memory without entering saved logs.

`UCKeyTranslate` maps a virtual key code, modifier state, and dead-key state to Unicode text. Apple discourages general application use in favor of `NSEvent.characters(byApplyingModifiers:)`. Neither API alone establishes a complete route from raw HID usages into arbitrary input methods. [Apple key translation API](https://developer.apple.com/documentation/coreservices/1390584-uckeytranslate)

`NSTextInputContext.handleEvent` supplies the normal text-system interface for mouse and key events. The input context communicates with an `NSTextInputClient`. Supporting input methods also introduces text insertion and marked-text operations that need their own external-control assessment. A successful ASCII typing test cannot establish support for composition, dictation, password managers, or assistive input. [Apple text input context](https://developer.apple.com/documentation/appkit/nstextinputcontext)

## Sandbox and permission limits

The browser currently enables App Sandbox and outgoing network access. It declares no USB or Bluetooth access entitlement. Apple documents `com.apple.security.device.usb` for USB devices, including HID devices, and a separate Bluetooth entitlement. These declarations do not establish access to every built-in keyboard or trackpad. [Apple sandbox hardware access](https://developer.apple.com/library/archive/documentation/Miscellaneous/Reference/EntitlementKeyReference/Chapters/EnablingAppSandbox.html)

The SDK documents Input Monitoring approval for listening through `IOHIDManager` and `IOHIDDevice`. The existing `HIDObservation` grant does not establish a grant for a new browser identity. Permission, sandbox eligibility, successful device open, and actual report receipt require separate observations. No permission request occurs in this research task.

`IOHIDManagerOpen` supports exclusive device seizure. The initial experiment does not need seizure. Global ownership can disrupt other applications and still does not establish human intent. A nonexclusive observer can test whether normal physical reports reach the candidate while its window has focus.

## Smallest experiment and rejection rules

1. Bind one physically identified pointer device and show an internal pointer driven only by its reports.
2. Route reconstructed click events through the normal application queue into one HTML button with an independent server counter.
3. Require the person to move and activate the button, with fresh trials and no typed text.
4. Attack the same button with CGEvent variants, accessibility actions, cursor warping, and the HID-manager posting option.
5. Repeat attacks during physical movement and button tracking, including device removal and newly appearing software devices.

An agent action rejects this candidate's input-blocking claim. Absent physical reports, failed human clicks, or missing new-identity permission leave the prevention result inconclusive. A successful narrow result supports only the measured device, event types, WebKit task, and OS build. Screenshots, accessibility disclosure, and general browsing compatibility remain separate requirements.

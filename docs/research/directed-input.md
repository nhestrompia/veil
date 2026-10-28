# Directed-input adapter diagnosis

Research date: 2026-10-23. This report reads saved trial files, current source, public Apple documentation, and the installed macOS 27 SDK. It posts no events and adds no runtime evidence.

## The old directed route also failed its controls

The saved `pid-hid` adapter never established a working control in the original committed native matrix. All three `InspectableControl` trials and all three `AgentFreeBrowser` trials in [the original evidence](../evidence/native-input-results.json) are inconclusive. Every directed trial has an empty submissions array. The original matrix therefore does not establish a regression from working directed input.

The new control trials also remain inconclusive. Their oracle records show partial event delivery, while the harmless form task never completes. This persistent adapter failure supplies no evidence of browser protection.

| Evidence set | Target | Directed trials | Accepted submissions |
| --- | --- | --- | --- |
| Original committed native matrix | `InspectableControl` | 3 inconclusive | 0 |
| Original committed native matrix | `AgentFreeBrowser` | 3 inconclusive | 0 |
| `artifacts/device-controls` | `InspectableControl` | 3 inconclusive | 0 |

## The new records isolate a missing click or focus step

Each new control oracle contains one trusted `pointermove` and thirteen trusted `keydown` events. None contains `pointerdown`, `pointerup`, `click`, `input`, or a submission. Thirteen keydown events match the adapter's twelve text characters plus Return. This count supports partial keyboard delivery. It does not establish text insertion.

The fixture subscribes to all those event types. The missing button events are therefore observable gaps, rather than events that the fixture never records. The page's passive telemetry listener does not cancel clicks or keys.

All three runs use the field center at screen coordinates `[454, 462]`. Their accessibility snapshots place the web area at `[100, 186]`. The recorded pointermove lands at page coordinates `[354, 276]`, exactly the difference. This agreement makes a blanket coordinate-flip explanation weak for the move event. It does not prove that the mouse-down event has correct window routing or focus behavior.

The accessibility snapshots precede the attempt. Their empty text-field values must not be presented as an after-action observation. The oracle's absence of `input` and submissions is the actual after-action evidence.

The files examined are `InspectableControl-pid-hid-0`, `-1`, and `-2` under `artifacts/device-controls`, with `.ax.json`, `.attempt.json`, `.oracle.json`, and `.log` suffixes. The logs contain ordinary browser startup lines and no defensive refusal. The attempt records report only that the probe attempted posting.

## Process delivery and window routing are different stages

`NativeProbe.post` chooses `CGEvent.postToPid` for every event in the directed route. `click` creates separate move, left-down, and left-up events at the same global point. It does not explicitly set click state, a matching down/up event number, or the target-window fields. The same helper uses ordinary global HID-stream posting for the working nondirected route.

Apple's SDK describes process posting as an event-routing mechanism. Its example taps events at the annotated-session location and forwards them to a chosen process. Events then pass through taps for that process. The contract does not promise that a raw newly constructed event receives every annotation that normal session routing supplies. [Apple process-posting API](https://developer.apple.com/documentation/coregraphics/cgevent/posttopid(_:))

The mouse constructor requires global coordinates. AppKit's event location, by contrast, uses the associated window's coordinate system. The existing recorded move supports keeping the current global point for a CGEvent calibration. Changing it to window-local coordinates without changing the construction method would introduce another uncertainty. [Apple mouse constructor](https://developer.apple.com/documentation/coregraphics/cgevent/init(mouseeventsource:mousetype:mousecursorposition:mousebutton:)), [Apple NSEvent API](https://developer.apple.com/documentation/appkit/nsevent)

Apple exposes `mouseEventClickState`, where one represents a single click. It also documents a shared event number for matching mouse-down and mouse-up events. The public enum includes `mouseEventWindowUnderMousePointer` and `mouseEventWindowUnderMousePointerThatCanHandleThisEvent`. The installed header identifies those window fields as public since macOS 10.7. These declarations justify a calibration with explicit annotations. They do not establish which missing field caused this failure or guarantee a correction. [Apple event-field API](https://developer.apple.com/documentation/coregraphics/cgeventfield)

AppKit's normal window dispatcher chooses a receiving view by hit testing and establishes first-responder behavior on mouse-down. A move reaching web content does not establish that the field received a down/up pair or became the text target. The missing click/focus step is the leading bounded diagnosis, not a proved kernel or WebKit defect. [Apple event architecture](https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/EventOverview/EventArchitecture/EventArchitecture.html)

## Key delivery does not guarantee text insertion

The Unicode adapter uses virtual key code zero for every character, then overwrites the event's Unicode string. Apple explicitly permits application frameworks to ignore that string and translate the virtual key code using their own perceived state. Therefore, trusted keydown telemetry alone does not prove that this text adapter must insert `native-input`. [Apple Unicode event setter](https://developer.apple.com/documentation/coregraphics/cgevent/keyboardsetunicodestring(stringlength:unicodestring:))

The existing physical-key-code adapter provides a useful comparison after focus succeeds. A fixed sequence remains specific to the supported keyboard layout. Neither Unicode nor key-code posting can supply text to an unfocused field merely because the page receives a keyboard event.

The directed route calls application activation and waits 300 milliseconds, but it does not verify foreground state. The nondirected route does verify foreground state. A fixed delay is not evidence that the expected key window and first responder exist. This difference remains a second calibration concern.

## Smallest next calibration

The next experiment uses a working global CGEvent click only to focus the field. It then posts keyboard events to the PID. This is a mixed route. Its label and evidence must never imply that the pointer portion uses process-directed delivery.

The comparison keeps the control build, fresh fixture, field coordinates, permissions, and target process fixed. It compares Unicode typing with the existing physical-key-code sequence. Separate stages record pointer delivery, text insertion, Return, and the server submission. A failed Unicode case alongside a successful key-code case would narrow the adapter problem to text semantics after focus.

If both mixed controls complete, the original all-directed pointer route still remains inconclusive. A later pointer calibration can use a verified window identifier owned by the research PID. It can add explicit single-click state, a matching event number, and the public window fields. That trial needs a fresh control result before any defensive-build interpretation.

If the mixed controls fail, diagnosis stops short of a browser claim. The next evidence would need to establish focus, actual key events at the target, and the text-system result. Private WindowServer calls or unrelated applications are unnecessary for this bounded question.

## The queue proposal did not survive its experiment

The earlier device-routing research proposed preserving an authorized event's exact object identity through the application queue. The parent experiment found that `postEvent` and `nextEvent` copied the event. That result rejects the proposed identity-preserving queue assumption.

The current keyboard prototype uses direct `NSApplication.sendEvent` dispatch for its internally authorized event object. Apple says applications rarely invoke that method directly, but the public contract permits the application dispatch path. Apple's stronger prohibition concerns direct calls to `NSWindow.sendEvent`. Those two methods must remain distinct. [Apple application dispatcher](https://developer.apple.com/documentation/appkit/nsapplication/sendevent(_:)), [Apple window dispatcher](https://developer.apple.com/documentation/appkit/nswindow/sendevent(_:))

This report does not change that implementation. It also does not upgrade the original directed probe's absent control into a successful block. The all-directed route remains uncalibrated.

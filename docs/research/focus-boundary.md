# Focus and visibility as external action routes

Research date: October 26, 2026. This note uses Apple documentation, WebKit source, and local fixture source. No UI, permissions, app binaries, or production code changed during this research.

The known input gate does not cover every signal that can start page JavaScript. A page can attach an action to window focus. The parent investigation reports three external actions after activation cycles, without accepted input or AX writes. The source trace below explains a matching mechanism. It does not establish that every activation path uses this exact sequence on the installed framework.

## Source trace

**AppKit facts:** `NSRunningApplication.activate(options:)` requests application activation. A successful request can make the application frontmost. `NSWindow.becomeKey()` reestablishes its first responder and posts `didBecomeKeyNotification`. The notification contains the window, with no `userInfo` dictionary. [Apple activation API](https://developer.apple.com/documentation/appkit/nsrunningapplication/activate(options:)), [Apple key-window transition](https://developer.apple.com/documentation/appkit/nswindow/becomekey()), [Apple notification](https://developer.apple.com/documentation/appkit/nswindow/didbecomekeynotification).

**WebKit facts:** `WKWindowVisibilityObserver` registers directly with `NSNotificationCenter` for window key/resign-key notifications. Its callbacks call `WebViewImpl::windowDidBecomeKey` and `windowDidResignKey`. Both notify `WebPageProxy` that `WindowIsActive` can change. Window ordering, occlusion, miniaturization, and view hierarchy changes also trigger activity updates. [WebViewImpl.mm](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/mac/WebViewImpl.mm).

**WebKit facts:** `WebPageProxy::updateActivityState` reads the page client. `dispatchActivityStateChange` sends `SetActivityState` to the content processes. `WebPage::setActivityState` forwards the state to WebCore's page. [WebPageProxy.cpp](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/WebPageProxy.cpp), [WebPage.cpp](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/WebProcess/WebPage/WebPage.cpp).

**WebCore facts:** `Page::setActivityState` calls `FocusController::setActivityState`. A change in the combined `IsFocused` and `WindowIsActive` state starts window and element focus/blur dispatch. These window events are not cancelable. The dispatch path does not require a keyboard, pointer, or AX action. [Page.cpp](https://github.com/WebKit/WebKit/blob/main/Source/WebCore/page/Page.cpp), [FocusController.cpp](https://github.com/WebKit/WebKit/blob/main/Source/WebCore/page/FocusController.cpp).

**Visibility facts:** Page visibility uses the separate `IsVisible` activity flag. Window activation alone need not change visibility. Visibility also depends on hidden ancestors, window visibility, and occlusion policy. A key-window experiment therefore does not cover the complete visibility route. [PageClientImplMac.mm](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/mac/PageClientImplMac.mm), [Page.cpp](https://github.com/WebKit/WebKit/blob/main/Source/WebCore/page/Page.cpp).

## Exact getter routes for the window experiment

Let `W` mean the active view's window and `V` mean the WebKit view. `PageClientImpl::activeWindow()` chooses a thumbnail's window first, then a pending move's target window. Otherwise it uses `V.window`.

The active-window expression is:

```text
W.isKeyWindow || (W != nil && NSApp.keyWindow == W)
```

`isViewFocused()` returns `WebViewImpl::isFocused()` when the implementation exists, otherwise false. These page-client expressions do not directly consult `NSApp.isActive`. [PageClientImplMac.mm](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/mac/PageClientImplMac.mm).

The view-focus getter returns true during its `becomeFirstResponder` implementation and false during `resignFirstResponder`. Otherwise it tests whether `V.window.firstResponder` equals `V`. It does not directly consult `NSApp.isActive` or `isKeyWindow`. [WebViewImpl.mm](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/mac/WebViewImpl.mm).

**Inference:** A diagnostic window that always reports `isKeyWindow == true` can keep the first branch of the active-window expression true. A false override does not necessarily force inactive state because the `NSApp.keyWindow` branch remains. Stable active-window state alone does not hold `IsFocused` stable. First-responder transitions remain a separate route.

**Inference:** Keep the hardware router's actual foreground-PID check independent of this logical window state. Otherwise the experiment changes who can receive hardware input while another application is frontmost. The local `DeviceKeyboardRouter.receive` currently checks both key-window state and the actual foreground PID.

**Source coupling:** `WebViewImpl::updateSecureInputState` tests key-window and view-focus state before releasing its owned Secure Event Input state. A logical-key override can affect password handling, not only DOM events. [WebViewImpl.mm](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/mac/WebViewImpl.mm).

**Test requirement:** Include password focus, real deactivation, window closure, and process cleanup. A result that leaves Secure Event Input owned in the background is not an acceptable browser fix.

## What an AppKit event filter can establish

**Apple fact:** `.applicationActivated` and `.applicationDeactivated` are subtypes of `.appKitDefined` events. [Apple event subtype documentation](https://developer.apple.com/documentation/appkit/nsevent/eventsubtype).

**Inference:** Refusing these events before `super.sendEvent` is a useful upstream experiment. It can affect the usual activation sequence. The documented subtype does not prove that all window changes arrive through that one dispatch method. WebKit listens to notifications and reads current window/responder state. Neither observer authenticates the caller as a human.

Instrument the refused subtype, real foreground PID, actual notification sequence, and authoritative action count. If the filter stops the action, also test normal physical reactivation and typing. A disabled or stale application state is not sufficient evidence of preserved browsing.

## Available controls and their limits

| Control | Source fact | Research conclusion |
| --- | --- | --- |
| Public WKWebView focus policy | The inspected public API does not offer a callback to approve each OS-driven DOM focus transition. [WKWebView documentation](https://developer.apple.com/documentation/webkit/wkwebview) | No supported selective focus filter emerged from this review. This is a bounded search result, not a universal impossibility claim. |
| `WebPageProxy::setSuppressVisibilityUpdates(bool)` | This internal C++ method suppresses queued activity updates. Immediate dispatch bypasses suppression. Releasing suppression schedules pending state. [WebPageProxy.cpp](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/WebPageProxy.cpp) | It is an engine research lead. It is not an Objective-C WKWebView selector. No corresponding wrapper appeared in the inspected C headers. |
| `_retainActiveFocusedState` | The private header describes preserving focus during hierarchy/responder transitions. Its declaration belongs to the iOS section. [WKWebViewPrivate.h](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/API/Cocoa/WKWebViewPrivate.h) | Do not assume that it exists or applies on macOS. |
| `_doAfterActivityStateUpdate:` | The private testing header declares a completion hook after an update. [Testing header](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/API/Cocoa/WKWebViewPrivateForTesting.h) | It observes completion. It does not deny the update. |
| Page loading deferral | Focus dispatch returns early when the page defers loading. [FocusController.cpp](https://github.com/WebKit/WebKit/blob/main/Source/WebCore/page/FocusController.cpp) | This is broad internal behavior. Normal protected keyboard operation under persistent deferral remains unproven. |

**Next experiment:** Test the scoped logical-key window against the same activation-only helper. Preserve real foreground checks and record first-responder changes. Then test focus/blur handlers in frames and visibility handlers under ordering and occlusion changes. A fix for the current armed page can establish a narrower blocked route. General browsing still needs those independent checks.

Upstream source can differ from the installed macOS framework. Runtime observations and binary identities must accompany any conclusion about this browser.

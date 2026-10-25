# Separate page activity from native input ownership

Research date: October 26, 2026. Source revision: [`94f9b7905e3ce9a3d7497f26b563adcad6b7525f`](https://github.com/WebKit/WebKit/commit/94f9b7905e3ce9a3d7497f26b563adcad6b7525f). This upstream revision does not identify the installed macOS framework. No apps, permissions, binaries, or production code changed during this review.

**Finding:** A stable offscreen host remains a research candidate. Source shows a private owner-aware release method, but no matching Objective-C method to rearm Secure Event Input independently. A deactivation reset alone does not prevent later background re-enablement.

## Exact visibility and focus inputs

**Source facts:** `PageClientImpl::isViewVisible(view, window)` returns false for a missing window or `view.isHiddenOrHasHiddenAncestor`. Normally it also requires `window.isVisible`. If occlusion detection is enabled, the window must contain the visible occlusion flag. A background-text-extraction configuration skips the latter two checks. This exception is not a general supported browser policy.

`isMainViewVisible()` uses the web view and its actual window. `isActiveViewVisible()` uses the active view/window, which can instead belong to a thumbnail or pending move. `isViewVisibleOrOccluded()` returns the active window's `isVisible`. `isViewInWindow()` only tests whether an active window exists.

The active-window test accepts `isKeyWindow`, or identity with `NSApp.keyWindow`. View focus normally compares the window's first responder with the web view. These getters contain no separate `NSApp.isHidden` or `NSApp.isActive` test. AppKit can still change their underlying values when an app hides. [PageClientImplMac.mm](https://github.com/WebKit/WebKit/blob/94f9b7905e3ce9a3d7497f26b563adcad6b7525f/Source/WebKit/UIProcess/mac/PageClientImplMac.mm#L165).

**Source fact:** The macOS private selector `_setWindowOcclusionDetectionEnabled:` controls occlusion detection. It does not bypass hidden ancestors or window visibility. [WKWebViewMac.mm](https://github.com/WebKit/WebKit/blob/94f9b7905e3ce9a3d7497f26b563adcad6b7525f/Source/WebKit/UIProcess/API/mac/WKWebViewMac.mm#L1905).

**Inference:** A constant logical key state only covers one activity input. A stable host must also preserve visibility and first-responder state. An offscreen position alone does not establish those invariants. Ordinary text/password delivery to such a host remains untested.

## Secure Event Input ownership and release

**Source facts:** `WebViewImpl::updateSecureInputState()` releases its tracked ownership when its window is not key or its view is not focused. Otherwise, password editor state enables ownership. Leaving a password field releases it. This code does not test the actual foreground PID or `NSApp.isActive`.

`resetSecureInputState()` conditionally disables its own tracked ownership and clears its internal flag. It does not change DOM focus. Resigning first responder and window closure call reset. WKWebView deallocation also calls reset. Key/resign-key notifications and becoming first responder call the update method. [WebViewImpl.mm](https://github.com/WebKit/WebKit/blob/94f9b7905e3ce9a3d7497f26b563adcad6b7525f/Source/WebKit/UIProcess/mac/WebViewImpl.mm#L2965), [WKWebView.mm](https://github.com/WebKit/WebKit/blob/94f9b7905e3ce9a3d7497f26b563adcad6b7525f/Source/WebKit/UIProcess/API/Cocoa/WKWebView.mm#L954).

**Exact private release API:** macOS WKWebView implements `-_resetSecureInputState`, which calls that owner-aware reset. Its internal macOS header declares the selector. Runtime availability still needs a check. [WKWebViewMac.mm](https://github.com/WebKit/WebKit/blob/94f9b7905e3ce9a3d7497f26b563adcad6b7525f/Source/WebKit/UIProcess/API/mac/WKWebViewMac.mm#L1589), [WKWebViewMac.h](https://github.com/WebKit/WebKit/blob/94f9b7905e3ce9a3d7497f26b563adcad6b7525f/Source/WebKit/UIProcess/API/mac/WKWebViewMac.h#L42).

**Rearm limit:** `didUpdateEditorState` requests reevaluation after a password-state change or an old `selectionType == None`. It also requires the new selection type to differ from `None`, which includes a caret. Unchanged password focus and ordinary typing do not guarantee reevaluation. [WebPageProxyMac.mm](https://github.com/WebKit/WebKit/blob/94f9b7905e3ce9a3d7497f26b563adcad6b7525f/Source/WebKit/UIProcess/mac/WebPageProxyMac.mm#L795).

**Search result:** No public or macOS Objective-C reevaluation method emerged from the inspected WKWebView implementation and private/internal headers. The C++ update method exists. Absence from this review does not prove that no other SPI exists.

**Inference:** A real return-to-key notification can rearm input protection without changing DOM state if logical activity remains constant. Its delivery and ordering require measurement. Background editor changes can also rearm ownership while logical key/focus remain true. Thus a single reset on deactivation is insufficient. Apple requires balanced ownership and release when another app becomes active. [Apple TN2150](https://developer.apple.com/library/archive/technotes/tn2150/_index.html).

## Smallest engine change if the app diagnostic fails

**Design proposal, not an implemented fix:** Put an explicit page-activity policy in `WebPageProxy::updateActivityState`. Hold the web-exposed focus/active/visible/in-window state separately from native window state. Apply it during creation, process recovery, and immediate updates. Existing queued-update suppression permits immediate updates and later flushes pending state. [WebPageProxy.cpp](https://github.com/WebKit/WebKit/blob/94f9b7905e3ce9a3d7497f26b563adcad6b7525f/Source/WebKit/UIProcess/WebPageProxy.cpp#L3519).

Keep Secure Event Input on actual native focus. Add one narrow owner-aware reevaluation API with an explicit actual-input eligibility value. On ineligibility, release ownership and prevent all editor callbacks from reacquiring it. On eligibility, reevaluate current password state before accepting a key. Keep the hardware router's actual foreground-PID check independent.

Acceptance needs unchanged DOM lifecycle state through external activation and hide/restore, usable physical text/password entry, protection before resumed password typing, and no background ownership. These tests establish the proposed boundary's behavior. They cannot by themselves prove agent-free behavior across every website or OS route.

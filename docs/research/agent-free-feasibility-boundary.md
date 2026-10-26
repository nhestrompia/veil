# Agent-free feasibility boundary

Checked 2026-10-26. This note extends the [process-signal research](process-signal-boundary.md). It makes no live prevention claim.

## Current conclusion

An ordinary same-user browser has no demonstrated defense against the measured renderer pause. Six calibrated browser trials produced website actions after external SIGSTOP/SIGCONT. Watchdog recovery also triggered the action. Hardened Runtime controls accepted the same signal operation. These are measured results on disposable research processes, not every release-browser configuration. [Browser evidence](../engine-process-pause-findings.md), [signing evidence](../signal-signing-findings.md).

Current Apple XNU source explains the default permission boundary. `cansignal_nomac` permits matching sender real/effective user IDs against target real/saved user IDs. The preceding `mac_proc_check_signal` call can deny access through operating-system policy. Thus matching IDs do not override every policy. `sigaction` rejects SIGSTOP handlers. This code supports the observed result but does not certify the exact installed kernel. [Apple XNU source, functions `cansignal` and `sigaction`](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/kern_sig.c#L283-L427).

No reviewed public API gives an ordinary target app its own signal-denial policy. This is a bounded research finding, not proof that every macOS design is impossible.

## Alternatives

| Option | Established fact | Project implication |
| --- | --- | --- |
| Hardened Runtime | Apple lists protections against code injection, library hijacking, and memory tampering. Our signed control still accepted pause/resume. | Retain it for integrity. Do not count it as signal denial. |
| App Sandbox | Apple describes restrictions on the sandboxed app, including termination of other apps. | Sandboxing the browser does not establish a restriction on an unrelated unsandboxed sender. This is an inference. |
| Endpoint Security | `AUTH_SIGNAL` authorizes signal requests. The ordinary client needs entitlement, root privilege, and TCC approval. | The existing prototype cannot enforce anything without those prerequisites and coverage tests. |
| Separate user ID | XNU's ordinary SIGSTOP permission test depends on real and saved IDs. Root senders pass that check. | A renderer under a different identity could reject an unprivileged sender. This remains an architectural hypothesis. |
| Clock changes | WebKit reads monotonic time for `performance.now()` and current time for `Date.now()`. | Changing one exposed clock cannot establish that every page loses timing information. |

Sources for the table: [Apple Hardened Runtime](https://developer.apple.com/documentation/security/hardened-runtime), [Apple App Sandbox](https://developer.apple.com/documentation/security/protecting-user-data-with-app-sandbox), [Apple signal authorization](https://developer.apple.com/documentation/endpointsecurity/es_event_type_auth_signal), [Apple client requirements](https://developer.apple.com/documentation/endpointsecurity/client), [Apple XNU](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/kern_sig.c#L283-L355), [WebKit performance clock](https://github.com/WebKit/WebKit/blob/main/Source/WebCore/page/Performance.cpp#L147-L159), [WebKit date clock](https://github.com/WebKit/WebKit/blob/main/Source/JavaScriptCore/runtime/DateConstructor.cpp#L153-L159).

### Separate identity needs a different architecture

A privileged helper that merely resumes the same-user renderer supplies recovery, not denial. Moving only that watchdog to another user leaves the renderer's signal permission unchanged. This follows from the target identity check and our recovery result.

A separate rendering identity needs privileged deployment and protected files. It also needs authenticated IPC and a display path. Apple's launchd manual permits `UserName` only for root-managed jobs. Current service registration requires administrator approval for launch daemons. Apple's daemon guide states that system-context daemons cannot present a graphical interface. These facts do not rule out a rendering service with a user-side display client. They do rule out treating a daemon as a direct replacement for the current GUI app. [Apple launchd manual](https://github.com/apple-oss-distributions/launchd/blob/main/man/launchd.plist.5#L120-L121), [Apple service registration](https://developer.apple.com/documentation/servicemanagement/smappservice/register()), [Apple daemon guide](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/DesigningDaemons.html).

A separate service also leaves the user-side host exposed to signals. Host interruption could still affect page state through IPC or display changes. That is an untested risk. No reviewed WKWebView API supplies a user-ID selector for its content process. This research does not establish a supported cross-user WebKit deployment.

### Clock changes need adversarial tests

A narrow `performance.now()` repair can suppress the current fixture without closing the capability. `Date.now()`, workers, media clocks, network messages, and server timestamps need separate controls. HTTP defines an independent server date, and applications can return their own timestamp bodies. A renderer patch cannot silently rewrite arbitrary authenticated application data while preserving its meaning. This last statement is an architectural inference. [WebKit clocks](https://github.com/WebKit/WebKit/blob/main/Source/WebCore/page/Performance.cpp#L147-L159), [HTTP Date definition](https://www.rfc-editor.org/rfc/rfc9110.html#section-6.6.1).

Disabling JavaScript or refusing network activity closes capabilities by removing normal website behavior. It does not meet the current general-web requirement. Likewise, this browser cannot prevent an agent from using its own separate HTTP client. The required boundary concerns actions and observations through this browser.

## Pinned engine seams

Local source inspection used WebKit commit `94f9b7905e3ce9a3d7497f26b563adcad6b7525f`. Current online sources corroborate the design but can change independently.

- `Source/WTF/wtf/CurrentTime.cpp:230,298` implements wall and monotonic clocks. The Darwin monotonic branch reads `mach_absolute_time()`.
- `Source/WTF/wtf/DateMath.h:86` defines `jsCurrentTime()`. `Source/JavaScriptCore/runtime/DateConstructor.cpp:110,154,169` covers date construction, date strings, and `Date.now()`.
- `Source/WebCore/page/Performance.cpp:158,163,171,189` covers public time, its origin, and conversion from engine timestamps.
- `Source/WebCore/page/LocalDOMWindow.cpp:836,841,851` supplies a frozen frame timestamp. `Source/WebCore/dom/Document.cpp:8949` passes it to animation callbacks. `Source/WebCore/dom/ScriptedAnimationController.cpp:143,156` exposes it to JavaScript.
- `Source/WebCore/platform/Timer.cpp:298,303` sets monotonic deadlines. `Source/WebCore/platform/ThreadTimers.cpp:112,128` reads the clock and reschedules repeating timers.

A candidate needs one consistent clock model across these paths. Workers and incoming event/resource timestamps need their own audit. Altering the global WTF clock also changes internal security deadlines and scheduling. Therefore a global replacement is not a small public-clock repair. These are source-based engineering inferences, not tested patch behavior.

An executable-only simulation can test an offset policy before an engine rebuild. Test monotonic output, wall/monotonic agreement, equal frame timestamps, deadline order, and repeated short pauses. Include long legitimate stalls and independent server time as counterexamples. The same observed gap can result from suspension or ordinary scheduling. A gap-only policy cannot identify its cause without another trusted signal. Clipping every large gap can hide one fixture while corrupting normal elapsed time. A simulation can expose these failures. Passing it establishes policy consistency only. It establishes neither WebKit coverage nor operating-system signal denial.

## Next implementable experiment

Extend the existing local timer fixture with independent wall-clock, worker, and server-time controls. Run matched native/stable trials without an engine change. Require stationary controls, zero admitted input, exact process identity, and cleanup. Only then consider a narrow clock patch. A successful patch would close measured routes, not prove arbitrary-page isolation.

Actual signal denial needs the missing Endpoint Security entitlement or a separately approved identity-isolation prototype. Neither route currently establishes agent-free behavior. This review made no permission, service, or operating-system changes.

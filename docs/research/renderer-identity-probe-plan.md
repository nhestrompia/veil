# Renderer identity probe plan

Checked 2026-10-26 against WebKit commit `94f9b7905e3ce9a3d7497f26b563adcad6b7525f`. Status: proposed same-user probe. No browser implementation or privileged execution occurred for this note.

The successful identity signal control supports a cross-user SIGSTOP boundary for disposable command-line children. It does not establish which credentials WebKit services receive. The earlier authorization covers no further root execution.

## Launch path and identity uncertainty

`ProcessLauncherCocoa.mm` selects named WebContent, Networking, and GPU services. It creates an XPC connection, assigns a one-shot instance, and sends bootstrap data with a Mach send right. After the launch reply, it gets the service PID from that connection. This is an XPC launch path, not direct child creation by the host. Apple documents that `launchd` manages XPC service launches. Host `fork` credential inheritance therefore cannot establish service identity. [Pinned launcher](https://github.com/WebKit/WebKit/blob/94f9b7905e3ce9a3d7497f26b563adcad6b7525f/Source/WebKit/UIProcess/Launcher/cocoa/ProcessLauncherCocoa.mm#L217), [Apple XPC guide](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingXPCServices.html).

The three macOS service templates specify `ServiceType=Application` and `JoinExistingSession=true`. Neither key supplies a measured real, effective, or saved user ID. The service entry point chooses an initializer from the bootstrap service name and checks the WebKit version. Changing a user-directory suffix changes neither the measured identity nor the signal rule. [Pinned content service](https://github.com/WebKit/WebKit/blob/94f9b7905e3ce9a3d7497f26b563adcad6b7525f/Source/WebKit/WebProcess/EntryPoint/Cocoa/XPCService/WebContentService/Info-OSX.plist), [network service](https://github.com/WebKit/WebKit/blob/94f9b7905e3ce9a3d7497f26b563adcad6b7525f/Source/WebKit/NetworkProcess/EntryPoint/Cocoa/XPCService/NetworkService/Info-OSX.plist), [GPU service](https://github.com/WebKit/WebKit/blob/94f9b7905e3ce9a3d7497f26b563adcad6b7525f/Source/WebKit/GPUProcess/EntryPoint/Cocoa/XPCService/GPUService/Info-OSX.plist), [bootstrap receiver](https://github.com/WebKit/WebKit/blob/94f9b7905e3ce9a3d7497f26b563adcad6b7525f/Source/WebKit/Shared/EntryPointUtilities/Cocoa/XPCService/XPCServiceMain.mm#L145).

This source trace does not establish the installed system framework's exact implementation. Each trial must record its actual framework paths and versions. A later custom-engine trial needs the existing engine identity checks for host and auxiliary processes.

## WindowServer distinction

The pinned WebContent initializer explicitly denies WindowServer connections on macOS. That does not establish that a host with `WKWebView`, or its GPU service, works outside a GUI login session. Apple's archived TN2083 explains that background applications can still depend on WindowServer and a GUI bootstrap context. Treat its historical connection details as context, not a current access guarantee. [Pinned content initialization](https://github.com/WebKit/WebKit/blob/94f9b7905e3ce9a3d7497f26b563adcad6b7525f/Source/WebKit/WebProcess/cocoa/WebProcessCocoa.mm#L871), [Apple daemon and agent contexts](https://developer.apple.com/library/archive/technotes/tn2083/_index.html#SECWINDOWSERVER).

Record the host's `SessionGetInfo` result and `CGSessionCopyCurrentDictionary` availability. Save only session identifiers, session user ID, and console/login flags. Apple distinguishes security session identity from the user ID. A session dictionary indicates context, not successful rendering. A missing dictionary or failed snapshot does not prove capture protection. [Apple session guidance](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPMultipleUsers/Concepts/FastUserSwitching.html#//apple_ref/doc/uid/20000776-103084), [Apple session dictionary API](https://developer.apple.com/documentation/coregraphics/cgsessioncopycurrentdictionary()).

## Smallest same-user probe

Build a separate disposable native app. Use one process pool, one nonpersistent data store, and one fixed-size `WKWebView`. Create no `NSWindow` and post no input. Keep inspection disabled. The nonpersistent store separates website data from normal sessions. It does not promise that all framework diagnostics avoid disk writes. [Pinned data-store contract](https://github.com/WebKit/WebKit/blob/94f9b7905e3ce9a3d7497f26b563adcad6b7525f/Source/WebKit/UIProcess/API/Cocoa/WKWebsiteDataStore.h#L49).

1. Record host credentials and session context before the web view starts.
2. Load a fixed inline fixture with a run nonce, colored rectangles, and a simple canvas. Reject other navigation.
3. After navigation completes, evaluate one fixed script for the nonce, DOM dimensions, and canvas pixel values.
4. Request a snapshot. Compare its dimensions and known colored pixels with the fixture, then save the disposable image.
5. Record exact auxiliary identities before releasing the view, pool, and store. Exit within a fixed deadline.

The host's JavaScript call is an internal diagnostic control. It supplies no external command endpoint. Apple documents JavaScript evaluation and asynchronous snapshots of web-view contents. These operations do not establish general web compatibility or interactive browsing. Record JS success and snapshot success separately. [Pinned JavaScript API](https://github.com/WebKit/WebKit/blob/94f9b7905e3ce9a3d7497f26b563adcad6b7525f/Source/WebKit/UIProcess/API/Cocoa/WKWebView.h), [Apple snapshot API](https://developer.apple.com/documentation/webkit/wkwebview/takesnapshot(with:completionhandler:)).

Use the view's `_webProcessIdentifier` and `_gpuProcessIdentifier`, plus the store's `_networkProcessIdentifier`. These are private research APIs, not a supported production identity interface. The network getter can create a lazy service. Record when it runs. A zero GPU PID means no identified GPU service, not successful isolation. A later bounded loopback request can test actual networking. [Pinned view identities](https://github.com/WebKit/WebKit/blob/94f9b7905e3ce9a3d7497f26b563adcad6b7525f/Source/WebKit/UIProcess/API/Cocoa/WKWebView.mm#L5558), [network identity getter](https://github.com/WebKit/WebKit/blob/94f9b7905e3ce9a3d7497f26b563adcad6b7525f/Source/WebKit/UIProcess/API/Cocoa/WKWebsiteDataStore.mm#L1220), [lazy network service](https://github.com/WebKit/WebKit/blob/94f9b7905e3ce9a3d7497f26b563adcad6b7525f/Source/WebKit/UIProcess/WebsiteData/WebsiteDataStore.cpp#L342).

For each reported PID, read its real, effective, and saved UID/GID with `PROC_PIDTBSDINFO`. Record its start time and executable path. Recheck identity after the task. Do not infer ownership from the process name or parent PID. XPC services need not be direct children. Missing metadata means unknown. Never terminate services by a global WebKit name match. Cleanup can terminate only the exact probe host it launched.

## Gate before any cross-user proposal

The same-user result must show correct JavaScript output, correct pixels, and identified service credentials. Otherwise, resolve that failure before another privileged proposal. Offscreen failure can justify a separate visible control in the disposable app.

A future isolated host must measure the credentials of every content, network, GPU, and replacement process. Host identity alone is insufficient. It must also establish session access, image delivery, and a restricted UI protocol. A vulnerable user-side UI process could preserve the pause attack. Same-user success supplies an instrumentation baseline. It proves no cross-user rendering, signal denial in WebKit, protected display, or agent-free browser.

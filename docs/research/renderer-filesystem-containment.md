# Renderer filesystem containment

Checked 2026-10-26 against current Apple documentation, the installed macOS 26.5 SDK, and pinned WebKit `94f9b7905e3ce9a3d7497f26b563adcad6b7525f`. This note combines source research with linked ordinary-user controls. These controls changed no privilege or privacy grant.

The measured ordinary-user control uses a separate App Sandbox app. Compare a transient `sandbox-exec` wrapper only as a diagnostic. Neither approach currently establishes a zero-write boundary for the whole WebKit process graph. The prior root authorization remains consumed.

## App Sandbox host

Apple supports App Sandbox through signed entitlements. Its current documentation states that first launch creates a container under `~/Library/Containers`. The app has read-write access there. macOS 14 and later associates containers with code signatures. A different signing identity can cause an access prompt or launch failure. Thus an ad-hoc-signed research app needs a distinct bundle identifier and a frozen build before its first test. The measured builds completed without a consent step. Future rebuilt identities still need a fresh launch check. [Apple sandbox configuration](https://developer.apple.com/documentation/xcode/configuring-the-macos-app-sandbox), [Apple container access rules](https://developer.apple.com/documentation/security/accessing-files-from-the-macos-app-sandbox).

The minimal control uses only `com.apple.security.app-sandbox=true`. The separate network comparison adds only `com.apple.security.network.client=true`. Neither main app uses `com.apple.security.inherit`. Apple reserves inheritance for child helpers and requires separate sandbox configuration for each XPC target. Add no app group, file-selection right, temporary exception, hardware right, or scripting right. Keep the network comparison distinct from the minimal control. A container or permission prompt ends the trial. This plan requests no additional consent. [Apple entitlement rules](https://developer.apple.com/library/archive/documentation/Miscellaneous/Reference/EntitlementKeyReference/Chapters/EnablingAppSandbox.html).

“Pipe-only” must describe the probe's own interface. It means fixed inline input and bounded output through preopened pipes. It does not mean the process cannot write to its container, or that platform frameworks and services never write caches. Keep inspection disabled, activation prohibited, and the same fixture, JavaScript, and pixel checks. Create no file chooser, bookmark, external URL route, command endpoint, or explicit window.

## Measured bootstrap failure and source hypothesis

The minimal app's temporary-file create/read/delete control passed. Opening the absolute workspace canary returned `EPERM`. Its content, GPU, and network getters returned zero after content termination. A LaunchServices comparison failed the same way. These results establish host filesystem controls and failed rendering, not service containment. The earlier relative-path `ENOENT` result remains inconclusive. [Absolute-path control](../../artifacts/renderer-filesystem-102-absolute/pair-1-sandbox/result.json), [launch-context comparison](../../artifacts/renderer-filesystem-102-launch-context/pair-1-sandbox/result.json).

The pinned `XPCServiceInitializerDelegate::checkEntitlements` has a macOS/Mac Catalyst guard. For a sandboxed client, it accepts `com.apple.security.network.client`. Without it, the code checks the caller's audit token for Mach lookup of `com.apple.nsurlsessiond`. A denied lookup rejects initialization. Comments identify this network requirement as a current limitation, including for file resources. This is a concrete mechanism consistent with the failure. The source trace does not prove the installed framework took that exact branch. [Pinned entitlement check](https://github.com/WebKit/WebKit/blob/94f9b7905e3ce9a3d7497f26b563adcad6b7525f/Source/WebKit/Shared/EntryPointUtilities/Cocoa/XPCService/XPCServiceEntryPoint.mm#L52).

Three fresh reference/network-sandbox pairs now pass. Each sandbox blocks its absolute workspace canary with EPERM, preserves its bytes, and passes its temporary-file control. JavaScript, snapshot pixels, stable identities, and process cleanup also pass. All roles still use user ID 501. The exact final signature contains only App Sandbox and outgoing-network entitlements. [Measured results](../evidence/renderer-filesystem-results.json).

The fixture remains inline-only. The network entitlement itself permits broader outgoing connectivity. Successful rendering supports the bootstrap hypothesis, but it does not establish an offline sandbox or service-wide filesystem containment. No root or privacy grant formed part of the comparison.

## Services do not supply the host's proof

Apple describes XPC services as separately managed processes with their own sandboxes. Its child-inheritance entitlement does not establish that a launchd service receives the same arbitrary host policy. The pinned launcher creates named WebContent, Networking, and GPU connections and exchanges bootstrap data. This source does not establish that launchd replays a custom host write-denial profile. Treat that transfer as unproven. [Apple XPC model](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingXPCServices.html), [pinned launcher](https://github.com/WebKit/WebKit/blob/94f9b7905e3ce9a3d7497f26b563adcad6b7525f/Source/WebKit/UIProcess/Launcher/cocoa/ProcessLauncherCocoa.mm#L217).

On macOS, pinned `AuxiliaryProcessMac.mm` independently builds sandbox parameters from home and Darwin temporary/cache directories. It derives a service-specific directory suffix, then compiles or loads and applies its service profile. This can involve profile caches outside the host's explicit output path. The installed framework's actual profile and extensions require measurement. The open source does not expose every shipping policy. [Pinned service sandbox setup](https://github.com/WebKit/WebKit/blob/94f9b7905e3ce9a3d7497f26b563adcad6b7525f/Source/WebKit/Shared/mac/AuxiliaryProcessMac.mm#L549).

Do not use the nearby UI-to-content/GPU temporary-directory extension code as proof of macOS grants. Those particular routes use iOS-family compile guards in this revision. macOS has the separate service initialization described above. Nonpersistent website data also leaves framework temporary/cache behavior unresolved. [Pinned content extension guard](https://github.com/WebKit/WebKit/blob/94f9b7905e3ce9a3d7497f26b563adcad6b7525f/Source/WebKit/UIProcess/WebProcessPool.cpp#L969), [pinned platform guard](https://github.com/WebKit/WebKit/blob/94f9b7905e3ce9a3d7497f26b563adcad6b7525f/Source/WTF/wtf/PlatformUse.h#L302).

## Transient sandbox-exec comparison

The installed Apple SDK marks `sandbox-exec` deprecated and directs app developers to App Sandbox. It applies a supplied profile before executing the command. It can test a narrow host write rule without changing the app's signature. It supplies no documented guarantee that the same rule constrains a separately launched WebKit service. [Apple SDK manual](/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk/usr/share/man/man1/sandbox-exec.1).

Use direct execution of the disposable host, not `open` or another launcher outside the profile. Bind the profile, host hash, and allowed test directory to the result. First test denial with a plain host file operation. Then test WKWebView. If WebKit fails, record the failure. Keep added capabilities in separate, source-supported comparisons. Do not enlarge file or Mach-service access merely to force a pass. A host denial proves that operation's result in that host, not a service-wide write boundary.

## What UID 501 can measure

1. Check the final signature, exact entitlements, sandbox status, and resolved home, container, temporary, and cache paths.
2. Compare a permitted container canary with a denied canary in a fresh ordinary directory outside it. Reject symlink escapes.
3. Run the inline JavaScript and snapshot checks through bounded pipes. Record any invisible framework window separately.
4. Read exact content/GPU/network PID credentials and start times from the ordinary controller. Sandbox-denied metadata remains unknown.
5. Compare scoped directory metadata and available open-file records before and after exit. Require complete host cleanup and record auxiliary lifetimes.

The controller must create only disposable canaries and inspect only this test's new container and known service directories. It must not scan unrelated app data. An absent open-file record misses files that already closed. Directory changes alone do not attribute a write to a PID. Sandbox logs describe observed denials, not every permitted write. A lack of logged writes cannot prove no writes. Apple provides diagnostics for violations, not a complete write audit. [Apple sandbox diagnostics](https://developer.apple.com/documentation/security/discovering-and-diagnosing-app-sandbox-violations).

## Boundary before any nobody proposal

App Sandbox does not assign a different Unix identity. Its UID-501 container result cannot establish where a `nobody` launch resolves its container. That account's password-record home, container setup, per-user caches, signing association, and inherited session remain separate questions. `HOME` and `TMPDIR` overrides alone cannot establish containment. [Apple home resolution source](https://github.com/apple-oss-distributions/CF/blob/main/CFPlatform.c), [Darwin directory resolution](https://raw.githubusercontent.com/apple-oss-distributions/Libc/main/gen/confstr.c).

The supported experiment can establish sandboxed host behavior and sampled service activity as the ordinary user. It cannot promise a writable private container for `nobody`, identical service policies, or zero external writes. Those remain explicit gates. No account, service, directory ownership repair, permission change, or administrator action belongs to this experiment.

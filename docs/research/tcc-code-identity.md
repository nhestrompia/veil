# TCC and code identity after a rebuild

Research date: 2026-10-25. This review reads repository records, installed SDK headers, and primary Apple sources. It changes no permission or signed artifact.

## A valid signature can fail a saved requirement

The browser's current ad hoc signature validates on disk. The reported executable SHA-256 is `43b1a9833d6c55b1e254b848f9bd09c202da46ba0f8d8833084df559e6a8a9d1`. Its current CodeDirectory hash is `0c7b32bc9890ace3d52519098021d6fbad3ad8e7`.

The root agent observed a grant write for that current requirement. A later check expected `89137ae7143d7facead823abc6a6f809629150d6` and returned `-67050`. These observations come from the active investigation. This review does not independently repeat its permission changes.

Apple defines `-67050` as `errSecCSReqFailed`. This means that the code fails a specified requirement. It does not, by itself, mean that the file's signature is corrupt. A static validity check can impose an additional requirement beyond signature validity. [Apple requirement-failure API](https://developer.apple.com/documentation/security/errseccsreqfailed), [Apple static validity API](https://developer.apple.com/documentation/security/secstaticcodecheckvalidity(_:_:_:))

The current artifact can therefore pass ordinary strict validation and fail an older hash requirement. Apple documents a hash requirement as specific to code with that hash. [Apple TN3127](https://developer.apple.com/documentation/technotes/tn3127-inside-code-signing-requirements)

## Ad hoc signing does not preserve update identity

The build scripts use `codesign --sign -`, which creates an ad hoc signature. Apple's designated requirement identifies later versions of the same code to authorization systems. An ad hoc requirement instead identifies a specific version. A stable bundle identifier and path do not replace that requirement. [Current build script](../../scripts/build.sh), [Apple requirement language](https://developer.apple.com/library/archive/documentation/Security/Conceptual/CodeSigningGuide/RequirementLang/RequirementLang.html), [Apple TN3127](https://developer.apple.com/documentation/technotes/tn3127-inside-code-signing-requirements)

A genuine Development or Developer ID signing identity can give successive builds a stable signing identity. Switching to that identity still changes the present code identity. It needs a separate consent check and does not restore the current grant automatically.

Do not replace the designated requirement with a bundle-identifier-only condition or an impersonated old hash. Such a change weakens the identity check without establishing valid consent.

The existing NativeProbe still works under its unchanged executable. That proves its own effective grants. It supplies no evidence that the rebuilt browser can monitor input.

## Two different caches must remain separate

Apple documents a kernel cache for code signatures. An updater that modifies signed executable files in place can leave cached information inconsistent with the new contents. Apple recommends a new temporary file followed by replacement. Its examples use inode numbers to distinguish replacement from an in-place overwrite. [Apple Updating Mac Software](https://developer.apple.com/documentation/security/updating-mac-software)

The root agent already repeated the installation with fresh files and inodes. The browser's access check still failed. This weakens a simple in-place update explanation. It does not identify which process retained the old requirement.

A saved authorization requirement, a live process's identity, and the kernel's file-signature cache are different observations. The reviewed public sources do not document a TCC cache invalidation API. They also do not promise that an off/on switch refresh replaces every retained identity object.

The stale requirement is therefore evidence for an identity mismatch. Calling its cause a confirmed TCC cache bug would exceed the available evidence.

## Safe diagnostics for the frozen artifact

These checks inspect the exact current bundle without launching it, signing it, or changing consent.

1. Record the executable hash, inode, modification time, bundle identifier, signing identifier, and designated requirement.
2. Run strict signature validation against the same bundle.
3. Evaluate an explicit requirement for the current hash.
4. Evaluate an explicit requirement for the older hash.
5. Save exit status and diagnostic text separately for each check.

The explicit requirement checks are read-only evaluations. They do not alter the embedded requirement. Apple documents this use of `codesign --verify -R`. [Apple TN3127 requirement evaluation](https://developer.apple.com/documentation/technotes/tn3127-inside-code-signing-requirements)

For this bundle, the two requirement expressions are:

```text
cdhash H"0c7b32bc9890ace3d52519098021d6fbad3ad8e7"
cdhash H"89137ae7143d7facead823abc6a6f809629150d6"
```

The expected result is current succeeds and older fails. That result would reproduce the mismatch outside TCC. It would not explain why TCC selected the older requirement.

The next live observation must preserve the same artifact. Correlate its exact PID, executable path, launch time, and TCC attribution for one bounded access check. The grant write and failure need the same service, subject, and request context before they form one causal sequence. Do not treat nearby log messages as one request solely because their times are close.

A public diagnostic can identify an existing process through `SecCodeCopyGuestWithAttributes` and its PID attribute. It can then use `SecCodeCheckValidityWithErrors` for dynamic validation. This needs no input event or device report. [Apple guest attributes](https://developer.apple.com/documentation/security/guest-attribute-dictionary-keys), [Apple Code Signing Services](https://developer.apple.com/documentation/security/code-signing-services)

`SecCodeCopySigningInformation` reads static signing information from disk even when given a running code object. Its ordinary hash output must not be labeled the kernel's cached process hash. Dynamic information requires the documented dynamic flag. The information call also does not validate a signature itself. [Apple signing information API](https://developer.apple.com/documentation/security/seccodecopysigninginformation(_:_:_:))

The root agent completed the existing-PID diagnostic without input or website use. Guest lookup and dynamic validity returned success. Associated static code and a fresh path lookup both reported the current hash. These results do not establish a kernel-cached hash or an effective Input Monitoring grant.

## Input Monitoring status remains the deciding check

Apple introduced `IOHIDCheckAccess` as a status query that does not trigger the approval prompt. The listening request type checks permission for keyboard event observation. The installed header returns Granted, Denied, or Unknown. [Apple WWDC19 explanation](https://developer.apple.com/videos/play/wwdc2019/701/?time=1995), [Apple access-check API](https://developer.apple.com/documentation/iokit/3181573-iohidcheckaccess)

The current browser logs a Boolean comparison against Granted. A false result therefore does not distinguish Denied from Unknown. A future controlled build can record the raw enum before it opens a manager. That new build needs its own identity and consent check.

An enabled System Settings row does not replace this runtime check. A separate helper's successful check does not query the browser's identity.

## A documented reset can remain limited to this app

Apple documents a reset with both a service name and a bundle identifier. Its current service list identifies `ListenEvent` as Input Monitoring. Without `sudo`, the default scope is the current user. The installed `tccutil` manual also documents the optional bundle identifier. [Apple reset guide](https://developer.apple.com/documentation/xcode/resetting-access-to-protected-resources-in-macos)

The narrow proposed command is:

```sh
tccutil reset ListenEvent research.agentfreebrowser.devicekeyboard
```

This command removes the saved authorization decision for that service and bundle. It grants no permission. Fresh user consent must follow through the exact current app. It does not change Accessibility, Screen Recording, or other apps' decisions under the documented scope.

The root agent will seek explicit approval before this reset. The previous approval covered the switch refresh and exact-path Add operation. This research executes neither a reset nor a new consent request.

A single approved reset followed by fresh consent is a reasonable next diagnostic because ordinary refresh attempts retained a mismatch. It is not a proven repair. Preserve the artifact, command status, and matched access result. Do not escalate a failure to `All`, an omitted bundle ID, `sudo`, direct database edits, or global service termination.

## Build lifecycle for later trials

The safer build workflow creates a complete new bundle, signs it once, and validates it before installation. It then replaces the previous files without modifying signed executable files in place. The bundle remains unchanged during permission diagnosis and attacks. Apple treats signed bundles as read-only after signing. [Apple signing guidance](https://developer.apple.com/library/archive/technotes/tn2206/), [Apple update guidance](https://developer.apple.com/documentation/security/updating-mac-software)

The probe's existing artifact cache already avoids needless signing changes. The browser can use the same principle while retaining its own source and signature checks. [Recorded cache milestone](../implementation.md)

If a stable signing identity is available, later development can use it through the normal signing workflow. That is a lifecycle improvement, not a demonstrated repair for today's mismatch.

No reset ran during this research. If the approved scoped diagnostic still fails, preserve the frozen artifact and exact request for Apple support. The cause remains unresolved until the request identity and selected requirement agree.

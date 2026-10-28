# First combined browser preview

Milestone 133 builds one AgentFreeBrowserPreview app from the shared browser sources. It combines the direct WKWebView renderer with ordinary-window sharing restriction, physical-keyboard routing, and the existing inspection, accessibility, export, and navigation policies. It uses no protected-video renderer or high-level backdrop.

The app is `dist/AgentFreeBrowserPreview.app`. Its separate bundle identifier is `research.agentfreebrowser.preview`. This is the first combined direct-rendering preview, not an agent-free claim.

| Part | Included behavior | Remaining evidence |
| --- | --- | --- |
| Capture | Window sharing set to none at ordinary window level | Physical visibility and external capture on this exact app |
| Keyboard | Existing device binding and exact-event gate | New app grant, physical completion, and same-session attacks |
| Inspection | Noninspectable WebView and disabled developer extras | External attachment checks on this app |
| Accessibility | Boundary application, window, and WebView types | External host and renderer reads on this app |
| Navigation | Address, history, reload/stop, and keyboard shortcuts | Physical keyboard navigation and broader website coverage |
| Exports | Existing clipboard, print, download, upload, and media restrictions | External export attempts on this app |

## Use and scope

The preview accepts HTTPS websites and loopback HTTP fixtures. It uses a nonpersistent website data store. A launch URL only fills the address field. External URL-open events are explicitly refused. Input Monitoring is never requested automatically.

After a separate grant, the intended sequence is Space to bind the built-in keyboard, then Return to open a prefilled address. Command-L selects the address. Command-[ and Command-] move through history. Command-R reloads or stops the page. Tab reaches page controls. The current router supports the measured built-in keyboard profile and US ASCII only.

Mouse input remains disabled. Input methods, key repeat, external keyboards, and a trained behavior classifier are absent. The app also restricts browser features that some websites need. General website compatibility remains unproven. Cross-user process isolation and the earlier lifecycle research are not integrated.

The app retains Hardened Runtime. It omits App Sandbox for the existing direct-device experiment. It installs no event tap or global input hook and uses no device seizure. The keyboard callback processes reports only while this app is frontmost and its window is key. Logs contain event categories and counts, not typed text or key codes.

## Verification

An invisible owner-driven harness compiles the same controller with a separate test entry point. It starts no HID reader and sends no system input. All 14 navigation and policy checks pass against a disposable HTTP fixture. They cover history, reload, stop, loading and error feedback, recovery, configured boundary types, effective content restrictions, ordinary window sharing restriction, and gated shortcut configuration. The host and three measured renderer processes exit.

The real preview then runs an unattended startup comparison. The matched control requests its fresh page once. The preview requests its page zero times and reports pending physical submission. Its startup log confirms ordinary window level, sharing restriction, content restrictions, disabled inspection, and no diagnostic input. Input Monitoring is off, so the runner keeps the verdict inconclusive. This is not a physical usability control or a calibrated agent-blocking result.

Address/response policy checks and exact-event dispatch checks pass. The latter cover one-time acceptance, copied-event and replay refusal, focus reset, and the address shortcut. Navigation regression checks also reject ambient, copied, and replayed shortcuts while each authorized event runs once. Swift 6 compilation with warnings as errors, strict signatures, Python compilation, and shell syntax pass. Existing granted helper images remain unchanged.

The first harness attempt stops before app launch because its output parent directory is missing. The runner now creates that parent. The successful rerun uses the already-built harness. This setup correction does not change the preview's behavior.

Review removes the initial navigation menu before consent. Navigation shortcuts now run only after exact-event admission inside the application dispatcher. The initial unapproved image and results remain archived. The final build repeats the navigation and real-app startup checks.

## Next acceptance gate

The new preview needs its own Input Monitoring grant. The existing DeviceKeyboardExperiment grant does not cover this identity. The [manifest](evidence/integrated-browser-permission-manifest.json) pins the exact image and records the unexecuted request. The builder refuses to overwrite that image.

After consent, keep this exact executable for physical page completion and external attacks. Test screenshot, accessibility, debugger, native-input, and export routes against the same session with readable controls. The existing NativeProbe can target research browser bundles for scoped window and accessibility reads. The capture-stress helper remains limited to InternalKeyboardControl. Its results do not transfer to the preview.

See [verification results](evidence/integrated-browser-results.json). Build with `scripts/build-integrated-browser.sh` before pinning. The owner-driven test command is `scripts/test-integrated-browser.sh` with a fresh absolute project artifact directory. The next work targets this single browser, with separate probes used only as attackers and controls.

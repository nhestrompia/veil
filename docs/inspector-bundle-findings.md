# Signed inspector client comparison

Milestone 148 compares the existing client as an ad-hoc signed app bundle. Its local target disappears about 51 milliseconds into the discovery loop. It finds no applications or fixture pages. The standalone control records target disappearance after about 55 milliseconds. This single comparison does not resolve discovery or establish browser protection.

The bundle uses the same diagnostic source and reference restrictions. Its identifier is research.agentfreebrowser.inspectordiscovery. It has no requested entitlement or macOS grant. A manifest pins its image and source hashes before the first launch. The runner checks the pinned identity, source hashes, and strict signature before future bundle launches. The builder refuses to overwrite the signed comparison image.

The new launcher waits for the app through LaunchServices. Its timeout cleanup stops only the verified helper executable and its launcher. Discovery success also requires helper cleanup. Tests cover that timeout and refusal of a changed bundle identifier or image. Nineteen relevant Python checks pass. Swift 6 compilation, strict signature, overwrite refusal, and Python compilation pass.

The exact bundled-client log query returns no matching events. That absence establishes no service acknowledgment or validation result. The CLI's earlier validation-failure evidence remains separate. Do not transfer that log result to this bundle or infer a required entitlement from either control.

The helper, reference, and fixture close. The oracle records zero task submissions. No debugger channel, script, capture, candidate browser, grant request, or administrator action occurs. The preview and granted recorder retain their pinned images.

The unpermissioned comparison app is dist/InspectorDiscoveryControl.app. It is a diagnostic client, not a new browser build. The bundle comparison requires --bundled alongside the existing runner options. Preserve this signed image and its manifest.

The next inspector work still needs a working external reference. Capture still needs valid owned coverage, then a fresh physical candidate session. Agent-free acceptance remains unmet. See [results](evidence/inspector-bundle-results.json), [manifest](evidence/inspector-discovery-app-manifest.json), and [lifecycle findings](inspector-lifecycle-findings.md).

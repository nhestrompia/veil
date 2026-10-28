# Build and distribution status

The repository contains source, test tools, reports, and selected evidence. `.gitignore` excludes `dist/`, `.build/`, and `artifacts/`. There is no portable browser release in this checkout.

## What runs now

The prepared test Mac has `dist/AgentFreeBrowserEngine.app` and `dist/InspectableControl.app`. The engine browser uses custom WebKit frameworks under `.build/webkit-engine/output/Release`. Its native bootstrap checks fixed paths and image hashes. The committed manifest records this Mac's paths.

Copying the app alone to another Mac does not supply that engine or satisfy those checks. A fresh clone also lacks compiled helpers. The current input policy covers the measured keyboard on the test Mac. Another Mac needs its own physical input controls and permission checks.

Do not present `scripts/build.sh` as the current browser build. It builds earlier variants. The engine work has a separate [build procedure](../engine/README.md), and [the current builder](../tools/build_focus_browser.py) pins a completed workspace engine. The builder refuses to replace an approved image. The recorded manifests are evidence, not portable installation settings.

A new-machine build needs a separately recorded build identity and local manifest. Do not edit historical evidence to label a rebuilt image as the tested one. The current checkout is not a one-command public installation.

## What to share for public testing

Publish compiled builds as versioned release assets. Keep source and evidence in Git. The browser download must include the patched WebKit runtime and all required resources, with paths that work outside this workspace.

Each release should include:

- The browser and readable control as separate, clearly named apps.
- SHA-256 checksums, source commit, engine revision, patch identity, and supported macOS/hardware details.
- Required third-party notices and source references.
- A test kit with the website runner, task prompts, result template, and test guide.
- Permission instructions and a record of the attack tests completed on that release image.

Sign and notarize a public download as part of the release workflow. Apple's [notarization guide](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution) describes the distribution process. Packaging, signing, and runtime hardening still need implementation and final-image tests here.

Do not include private fixture-controller keys, personal browsing data, macOS permission databases, local profiles, or developer credentials. Testers grant permissions directly on their own Macs.

The existing app is ad hoc signed without Hardened Runtime and depends on the workspace engine. It is a local research build. A portable release is the next distribution deliverable, not an existing download.

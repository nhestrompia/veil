# Implementation milestones

## Milestone 1: native research shell

Implemented October 23, 2026, on macOS 26.6, build 25G72, arm64, with Apple Swift 6.4 and the macOS 27 SDK.

The browser contains one WKWebView with inspection disabled and a nonpersistent website data store. It exposes no external page-read, snapshot, or evaluation API. A separate control binary enables inspection at compile time. Both app bundles use Hardened Runtime, an ad hoc signature, App Sandbox, and network-client access. This is a research build, not production distribution.

The loopback fixture owns submission outcomes outside the browser. Controller requests need a random key in a local, ignored file. This prevents accidental validation through browser state. It does not isolate the fixture from unrestricted same-user code. Direct HTTP submissions are oracle tests, not browser-attack evidence.

Two architecture sketches and an independent judge compared direct Swift compilation with SwiftPM. The judge preferred the Python fixture and separate executables. The implementation keeps those boundaries and uses direct compilation for the smallest first build. A Swift HTTP server and a shared browser/attacker library were rejected as unnecessary initial work.

Verification completed:

- Both signed app bundles compile with Swift 6 and warnings treated as errors. Signature verification passes.
- Twelve policy cases cover HTTPS, loopback HTTP, and rejected schemes or hosts.
- The fixture test covers controller authorization, independent trial outcomes, and removal of typed data from event telemetry.
- The protected app loaded the loopback page. Native computer use inspected its window and followed its HTTPS link to example.org.

The native tool exposed the fixture's accessibility content despite disabled inspection. This is an early observation, not a prevention result. Milestone 2 measures reads and actions with an independent oracle.

No human-input baseline, Safari inspector attachment comparison, or capture exclusion result is established by this milestone.

## Run the prototype

```sh
bash scripts/build.sh
bash scripts/test-policy.sh
python3 -m unittest discover -s tools -p 'test_*.py' -v
python3 tools/fixture.py
open -n dist/AgentFreeBrowser.app --args --url https://example.org
```

Use `dist/InspectableControl.app` only as the separate inspection-positive control. The browser accepts HTTPS and loopback HTTP. Clipboard operations remain available for baseline attacks. Export restrictions and input defenses are not implemented yet.

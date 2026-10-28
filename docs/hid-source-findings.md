# Keyboard source policy

The keyboard router now checks device ancestry before it accepts a binding gesture. It rejects known software sources and unknown device paths. The first supported profile is this Mac's observed built-in keyboard, with its FIFO transport and specific Apple service ancestry.

This is a narrow research policy. It does not establish human intent, cryptographic device authentication, or support for other keyboards.

## Why transport and a virtual flag are insufficient

The read-only audit found three relevant services. The measured keyboard used the expected Apple FIFO chain. A software user device reported USB transport and a true virtual-device marker. A system keyboard shim had neither transport nor that marker.

The policy refuses software ancestry through the actual kernel class API. It checks conformance to `IOHIDUserDevice`, `IOHIDResourceDeviceUserClient`, and `IOHIDSystem`. These checks do not trust a caller-supplied `IOClass` property. They reject the observed software services even when a descriptive field is absent.

The observer accepts one parent per node and stops at a parentless registry root. Malformed property types, unreadable nodes, alternate parents, incomplete ancestry, and traversal beyond 24 nodes produce an unavailable result. The allow rule also requires keyboard usage and the measured FIFO prefix. Unknown sources never bind automatically.

The [primary-source review](research/hid-origin-guarantees.md) explains the developer and private entitlement paths. It also distinguishes published source behavior from this installed macOS build. The [audit evidence](evidence/hid-source-audit.json) records the actual classes and decisions.

## Code and checks

`HIDSourceSnapshot` reads registry classes and limited properties. `HIDSourcePolicy` makes the decision. The router applies that decision before it binds an `IOHIDDevice`. The existing process-private event identity gate remains in place. Device removal clears binding, and focus loss clears pending input.

Twelve source-policy cases pass. They cover the supported profile, software ancestry with copied metadata, explicit virtual markers, missing transport, unknown classes, partial ancestry, wrong usage, and unavailable observations. The read-only audit classifies one observed keyboard as eligible and two software paths as refused. It opens no device and collects no input.

The full device browser compiles with Swift 6 warnings as errors. Its event-dispatch checks pass, and all 32 Python checks pass. The candidate binary is in `.build/device-keyboard-source-policy`. The installed browser and NativeProbe remain unchanged, so this milestone does not refresh or expand grants.

## Limits and next validation

The current desktop references are unavailable. No live input attack or physical task ran on this revised candidate. A policy decision on registry metadata does not replace those controls. The next installed build needs its existing device grant checked again, followed by physical navigation and matched external attacks.

Other hardware, mouse input, Unicode text, assistive access, capture protection, and remote inspector attachment remain separate gaps. The source rule reduces a known software-binding risk. Agent-free status remains unproven.

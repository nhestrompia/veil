# Veil normal mouse input

Milestone 156 changes the mouse interaction at the user's request. The new app is `dist/Veil.app`, bundle `research.agentfreebrowser.veil`. It uses the normal macOS cursor. It has no green pointer and requires no Command-Option-M shortcut.

## Input boundary

Fresh reports from the measured device profiles authorize mouse actions while Veil has focus. A neutral movement or wheel report selects the device automatically. Focus loss, geometry changes, navigation, sleep, removal, malformed reports, and stale timestamps reset that session. A later physical movement can start it again. Ordinary software mouse and wheel events remain refused.

Veil uses the system cursor position at a physical press. The user explicitly selected this boundary. Software can move that cursor, so it can redirect a click that a human physically makes. Physical input does not attest the human's intent. Apple documents cursor movement without mouse events. [Apple cursor APIs](https://developer.apple.com/library/archive/documentation/GraphicsImaging/Conceptual/QuartzDisplayServicesConceptual/Articles/MouseCursor.html)

The implementation opens no exclusive device, installs no event hook, and never hides, disassociates, or warps the system cursor. Reports outside the owned content area cannot trigger a page or toolbar action.

## Implemented scope

- Primary clicks at the normal cursor, including native toolbar controls.
- Hover from physical motion reports.
- Vertical wheel reports from the measured USB mouse.
- Automatic activation and recovery after focus or navigation changes.

Drag, secondary and double clicks, modifier clicks, horizontal scrolling, and multitouch trackpad gestures remain unsupported. Wheel acceleration, momentum, direction preferences, screen-coordinate metadata, and other devices need compatibility tests. The keyboard still uses the measured built-in device and US ASCII.

## Verification

The new packet/state tests pass signed wheel values, malformed packets, neutral startup, paired clicks, outside-window cancellation, movement cancellation, lifecycle reset, and stale-report refusal. The existing 2,010 offline adversarial pointer checks still pass.

The first real WebKit control failed to deliver hover and wheel despite admitting the internal events. Private routing now delivers them directly to the owned target view. A nonzero-window-origin check then exposed incorrect wheel coordinates. The final control verifies client coordinates 320,170 and records one webpage click, one native button click, one pointer move, and one wheel event that scrolls 120 points. It also refuses five forged direct or queued events. This control opens no HID reader and posts no OS input. It does not establish physical usability or defeat an external agent.

All 73 relevant Python checks pass. The new app builds and its sources match its manifest. Both earlier permissioned browser images retain their hashes. The new app's no-request preflight reports Input Monitoring off. The user then approves this exact image's permission request. The request initially leaves access off. The user enables Veil manually, and a fresh LaunchServices preflight confirms permission=true. A bounded physical mouse/wheel session is open for the next control; the native UI tool cannot start.

Physical click/wheel verification and external-agent tests on this exact image remain pending. Earlier model and capture results do not transfer automatically. The old unattributed click remains unresolved. [Manifest](evidence/veil-browser-manifest.json) · [Control results](evidence/veil-normal-mouse-results.json)

## Run the new app

After granting this app Input Monitoring, launch on the prepared test Mac:

```sh
open dist/Veil.app --args --url 'https://www.google.com/'
```

Select Veil. Use physical Space, then Return on the built-in keyboard to load the address. Move the physical mouse normally. No separate pointer activation is needed.

For a bounded physical click and wheel control:

```sh
python3 tools/run_preview_session.py --veil --surface physical-mouse \
  --output artifacts/my-veil-mouse-session
```

The fixture records a click and wheel/scroll events. The window closes after fifteen minutes. This runner requires an approved effective grant and cannot substitute software for the physical control.

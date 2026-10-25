# PID-scoped passive keyboard control

The new observer route uses Apple's tapCreateForPid API with listenOnly and a keyDown-only mask. The OS routes that tap to the exact research PID. The callback also requires foreground ownership and the fifteen-second deadline before decoding text. It neither posts nor changes an event. [Apple PID tap API](https://developer.apple.com/documentation/coregraphics/cgevent/tapcreateforpid(pid:place:options:eventsofinterest:callback:userinfo:))

This avoids the AppKit adapter's missing window ownership metadata. The original AppKit route keeps its strict filter. No fallback reads unowned events.

## Generated reference result

The readable reference accepted one task through generated fake input. The PID-scoped listener received thirteen key events and matched native-input. It saved no raw text or key codes. The listener removed its tap on completion. Both process cleanups passed.

This is a working software observation control. It does not establish whether the observer can read physical keys, or whether it can disclose a protected page marker. No candidate observation or successful physical reference followed from this control. The [saved results](evidence/keyboard-pid-observation-results.json) preserve those qualifiers.

## Permission recovery

Rebuilding the observer invalidated its effective grant. System Settings still showed its switch on. Exact-bundle Add alone did not restore access. The user explicitly approved this app-only command:

```sh
tccutil reset Accessibility research.agentfreebrowser.keyboardobserver
```

The reset succeeded. Re-adding the exact app restored effective Accessibility and listening access in a fresh app preflight. No other permission reset. The browser and NativeProbe stayed unchanged.

Automatic approval review initially rejected the reset because the earlier approval covered Add only. That rejected attempt did not run. The user's later explicit reset approval resolved it.

## Reproduce the generated control

```sh
python3 tools/run_keyboard_observation.py --output artifacts/observer-new-control --mode pid
```

The output directory must not already exist. The controller requires a clear desktop input guard and working NativeProbe grants. It accepts either normal Accessibility label attribute, skips input after early observer failure, and verifies exact cleanup. Three new checks enforce task completion, phrase matching, and completed cleanup. All 55 Python checks pass.

The observer app is now frozen for physical controls. Its executable hash is 31c0103400276d78af848072760d224442a7a3c0c6bd62d1a186a20121777cc0. Do not rebuild it before that comparison.

## Physical timing attempts

The first operator sequence finished before listener start. A fresh attempt failed foreground checks before tap creation. Another listener expired before the operator could type. No valid physical reference emerged. Every reference process passed cleanup.

Those results remain inconclusive. The next controller must let the person start observation from the page, with a visible ready state. Chat delivery cannot supply that timing guarantee.

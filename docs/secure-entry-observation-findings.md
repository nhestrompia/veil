# Secure password entry observation control

The observer recognized generated ordinary text but received no keys during completed password tasks. This experiment uses the readable control. It does not modify the restricted browser or enable Secure Event Input directly.

## Method

The fixture accepts an optional `field-kind=password` query. All other task behavior and the independent oracle stay the same. The controller locates the labeled field, waits for actual tap readiness, and sends the fixed fake sequence through the frozen NativeProbe.

The input probe launches in the background. This avoids transient probe activation that could terminate a focus-scoped listener. The report records whether the observer still runs after input returns. It also queries the existing Secure Event Input state after the attempt and after process cleanup. These checks read one system boolean and change no state.

The initial ordinary and password trials ended on focus loss. Their evidence remains separate. A zero-event password result with uncertain input timing does not establish protection. The background-launch comparison adds the missing observer-liveness evidence.

## Results

On macOS 26.6, build 25G72, the background-launch ordinary reference completed one task. Both matchers succeeded from thirteen events. Secure Event Input was off. The observer remained alive after input and ended after its fifteen-second collection interval.

Two background-launch password trials each completed one task with zero observed keys and neither phrase match. Secure Event Input was active after input. Both observers remained alive after the input probe returned. The last trial also verified one accepted oracle action before that liveness check.

The password listeners ended on later focus loss before their first received key. Their collection clock therefore never started. These results show zero delivery through this listener during the completed generated tasks. They do not establish an uninterrupted fifteen-second physical password sample.

Every observer and reference passed cleanup. Secure Event Input was off after each reference closed. The browser, NativeProbe, and observer executables remained unchanged. The [saved comparison](evidence/secure-entry-observation-results.json) includes the initial focus-limited attempts and the repaired background trials.

The observer SHA256 was `cdd1829e60dd838f5a2b1ef91f9d5635e7f61760360f9c18c494f8eb90086aac`. The readable control SHA256 was `421bc9c112794974170199b91f73d614ed913263a44abc1df96972c5988dbf10`.

## Scope

These are generated-input controls. They do not replace physical password-entry samples or prove confidentiality in DeviceKeyboardExperiment. They test one PID-scoped passive listener. Other observation methods remain separate.

Apple TN2150 describes Secure Event Input for private entry and warns against general-text or application-lifetime use. See [Apple's archived note](https://developer.apple.com/library/archive/technotes/tn2150/_index.html). WebKit source enables it for focused password fields and disables it on ordinary focus or reset. See [WebKit's macOS implementation](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/mac/WebViewImpl.mm#L2694).

This experiment adds no whole-browser secure-input mode. The confirmed physical ordinary-text observation remains an unresolved gap.

## Reproduce

Run the two commands sequentially with fresh output directories:

```sh
python3 tools/run_keyboard_observation.py --output artifacts/ordinary-entry --keycodes --field-kind ordinary
python3 tools/run_keyboard_observation.py --output artifacts/password-entry --keycodes --field-kind password
```

The local fixture must already run. NativeProbe and KeyboardObservationProbe must retain their effective existing grants. No permission request runs. All 66 Python checks and the Swift matcher and timing checks pass.

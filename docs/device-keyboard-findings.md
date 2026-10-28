# Keyboard-only device routing

These results describe the first keyboard-routing binary. The revised [startup workflow](launch-navigation-findings.md) needs a new physical control and attacks against that same process.

DeviceKeyboardExperiment compiles, passes signature checks, and opens its device reader with the approved Input Monitoring grant. Its event-dispatch checks pass. The user completed one website action through physical typing. Twenty matched generated-input trials then stopped, with four further trials inconclusive. This is a keyboard experiment, with mouse input disabled.

## Input path

The application rejects ambient input events before normal application dispatch. A raw keyboard callback can create an internal NSEvent for one dispatch. The gate checks the exact retained object. Matching content, timestamps, source fields, or a recent period of physical activity cannot authorize another event.

The first queue experiment failed. `NSApplication.postEvent` followed by `nextEvent` returned a different object on this machine. The implementation therefore uses direct `NSApplication.sendEvent` dispatch. It keeps the normal application-to-window path and never calls `NSWindow.sendEvent` directly.

The [dispatch checks](evidence/device-dispatch-check.json) cover exact-object acceptance, one-time use, copy rejection, and reset. These checks do not establish delivery into WebKit. The independent fixture accepted one action after the user reported physical completion. The same browser process remained alive for all attacks.

## Device binding and limits

A Space report binds one keyboard object for the session. Later reports must come from that same object. Device removal invalidates the binding and pending events. Loss of foreground focus clears pending events and transient key state. The code processes reports only while its own window is key and its process is frontmost.

This bootstrap does not authenticate a person or device. An attacker that supplies an eligible report during binding remains a required test. Device binding alone does not establish human intent. The [routing research](research/device-routing.md) describes report-producing attacks and the limits of descriptive device properties.

This first version supports US ASCII, basic navigation keys, and modifier state. It has no pointer route, input-method support, or key repeat. It cannot serve as the general browser MVP.

The research host omits App Sandbox because this experiment opens devices directly. It retains Hardened Runtime and uses a separate identity. Other browser variants keep their sandbox. A future helper design would need a separate trust-boundary test.

The grant permits broader keyboard access than the app's focus rule. The code keeps key usages and text transient in memory. Saved logs contain categories and counts. They omit typed text, key codes, and device names.

## Same-session test

The helper keeps one browser process alive after physical calibration. It requires a declared physical completion, a bound device, and an accepted independent website action before attacks. It counts only new submissions. The disposable page clears its field after accepted actions.

The [adapter controls](evidence/device-input-controls.json) include twenty successful trials and four inconclusive trials. Directed PID input failed three controls. One curved-input control also failed. Missing controls cannot support blocked verdicts. The runner preserves those limits and stops after unexpected admitted input that leaves uncertain form state.

```sh
bash scripts/build.sh devicekeyboard
bash scripts/test-device-queue.sh
python3 tools/run_device_session.py start
python3 tools/run_device_session.py attack --operator-physical-completion-confirmed
python3 tools/run_device_session.py stop
```

The confirmation flag records the operator's declaration. It does not certify physical origin. Run the attack command only after that declaration and actual website completion. A rejected event without usable physical input remains inconclusive.


## Same-session results

The [physical control](evidence/device-physical-control.json) records the user declaration, browser hash, and independently accepted action. The [attack results](evidence/device-session-attacks.json) contain 24 attempts against that same calibrated process. None produced a new accepted submission or an admitted input event.

Twenty trials recorded refusal with working matched controls. Three directed-PID trials and one curved-input trial remain inconclusive because their controls failed. The tested state sources include session, HID, private, curved HID, and physical-key-code events. Both lower-level IOHIDPostEvent variants also stopped in all three matched trials.

This is the first usable keyboard-path result in this project. It does not establish an agent-free browser. The build still loads URLs from launch arguments without physical confirmation. That is a separate automation route to close. Pointer support, device-binding attacks, full accessibility coverage, and capture behavior on this exact build remain unfinished.

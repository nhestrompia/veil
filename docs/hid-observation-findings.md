# Raw device input experiment

Status: the observer compiles and passes signature checks. Its Input Monitoring grant is absent. No physical baseline or input defense exists yet.

The user approved the Input Monitoring request. The request API ran, but the effective grant remained off. The native tool could not find a System Settings window in the reported locked session. The setting still needs completion in an accessible desktop session.

The experiment tests whether device values offer evidence that ordinary CGEvent source fields cannot supply. It keeps this measurement separate from a mouse-behavior classifier. See the [remaining-boundary research](research/remaining-boundaries.md) for the API contracts and adaptive attacks.

## Observer

`HIDObservation.app` uses IOHIDManager to match keyboards, mice, and pointer devices. A local event monitor records application events separately. Raw callbacks run on the scheduled main run loop.

The observer saves data only while its own window has focus and its process is frontmost. Saved records contain timestamps, event categories, pointer coordinates or values, and temporary device ordinals. Keyboard usage IDs, key values, key codes, typed text, and device names remain absent from the file. The observer limits each collection to 10,000 records and reports that limit in its output.

The OS permission itself permits broader device access than this collection policy. The separate app has no browser session, networking code, or Accessibility grant. Its permission command requests only Input Monitoring. It does not request permission when the ordinary Start button finds that access is absent.

The native form accepts only the fake value `native-input`. Its accepted-action count checks whether the synthetic adapter operated the form. This count is local instrumentation, not the browser fixture's independent oracle.

All saved datasets keep `humanBaselineVerified` false. A tool-driven run cannot certify a physical baseline. A person must supply physical movement, clicks, and fake typing for that comparison.

## Virtual-device check

The separate `VirtualDeviceProbe` attempts `IOHIDUserDeviceCreateWithProperties` and `CoreHID.HIDVirtualDevice` creation with a standard keyboard descriptor. It never activates a device or sends an input report. Its ad hoc signature has no entitlements.

Both APIs returned nil in all three repetitions on macOS 26.6, build 25G72. The [saved results](evidence/virtual-device-results.json) include the binary hash and empty entitlement set. Apple documents an entitlement requirement for virtual-device creation. This test has no entitled positive control, so it does not prove that entitlement checking caused every refusal. It also does not close other synthetic-input routes.

## Next measurement

```sh
bash scripts/build-hid-observation.sh
bash scripts/build-hid-attack.sh
open -n dist/HIDObservation.app --args --permissions --out "$PWD/artifacts/hid-permissions.json"
```

After approval and an effective grant, the observer can collect a bounded session.

```sh
open -n dist/HIDObservation.app --args --observe --duration 30 --out "$PWD/artifacts/hid-observation.json"
```

A person can move the pointer, click the field, type `native-input`, and click **Record action** while the window stays focused. Separate synthetic sessions need the existing native adapters and a working action control. Physical input must remain absent during those synthetic sessions, or the dataset needs a mixed-input label.

The first useful comparison counts device values and app events from each source. No classifier or blocking threshold follows from event counts alone. Raw reports do not establish human intent. Event taps, cursor redirection, reused reports, accessibility actions, and lower-level posting still need adaptive tests before an input rule can support the goal.

The synthetic runner uses an eight-second collection for each adapter. It reports an observation only after the fake native form accepts the value and collection stops. It never reports agent prevention.

```sh
python3 tools/run_hid_observation.py --repetitions 3 --output artifacts/hid-synthetic
```

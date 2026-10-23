# Lower-level event posting

Both IOHIDPostEvent variants completed the fake action in all three trials. The observer reported no raw device values in any trial. This result measures the current OS and observer configuration. It does not establish that every HID callback has a physical source.

The separate probe opens an IOHIDSystem parameter connection. It uses the existing approved event-posting grant. A CGEvent click focuses only the research field. The probe then types the fake value and Return through IOHIDPostEvent. It checks research foreground ownership before each post and closes the connection after the sequence.

| Option | Accepted fake action | Posts returned success | Raw keyboard observations |
| --- | --- | --- | --- |
| Default options | 3/3 | 78/78 | 0 |
| HID-manager report option | 3/3 | 78/78 | 0 |

The deprecated API remains part of the attack test. The build preserves its compiler warning. It does not enter the browser implementation. Neither variant requests a new grant or sends input to another app.

The [saved results](evidence/hid-posting-results.json) retain all return codes and the probe hash. The observer's accepted count is local instrumentation. It is not the independent website oracle. The tests do not prove physical inactivity during collection.

Apple source contains a report-generating path for the HID-manager option. These runs did not observe such reports. The reviewed source may differ from this OS, or another delivery constraint may apply. No instrumented driver trace resolves the cause. See the [routing research](research/device-routing.md).

A future device gate must bind a selected device and test bootstrap, replacement, and report-producing attacks. Accepting any callback, or opening a time window after physical activity, remains an unsupported rule.

```sh
bash scripts/build-probe.sh
python3 tools/run_hid_observation.py --routes iohid-legacy iohid-reports --repetitions 3 --output artifacts/hid-lower-posting
```

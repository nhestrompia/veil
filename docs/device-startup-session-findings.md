# Physical startup and expanded attacks

The revised visible-control browser completed the physical startup task. The user selected the app, bound the keyboard, opened the pending address, typed the fake token, and reported completion. The independent fixture recorded one accepted action. The same process remained alive for the attacks.

The [physical record](evidence/device-startup-physical-control.json) identifies the process and binary. This build enables window sharing for diagnosis. It retains the keyboard gate and Accessibility overrides. Its visibility setting deliberately permits page capture.

| Route family | Completed attack trials | New accepted actions | Result |
| --- | --- | --- | --- |
| Nine calibrated native routes | 27 | 0 | Input refused |
| Two all-directed PID routes | 6 | 0 | Inconclusive, controls failed |
| Screenshot, OCR, curved HID input | 3 | 0 | Input refused, page disclosed |

The [native results](evidence/device-expanded-session-attacks.json) contain 33 trials. No trial admitted an input event. The gate recorded 1,227 refusals. All blocked verdicts require a working matched control. The original all-directed PID route and its window-annotated variant still lack successful controls. Their six failures cannot establish prevention.

The [vision results](evidence/device-startup-vision.json) contain three successful control tasks and three candidate attempts. Each agent captured only the target window, found its label through OCR, and derived field coordinates from the public fixture layout. All three screenshots disclosed the fake marker. Generated input still produced no new accepted action or admitted input event. Disclosure remains a failure of the stronger agent-free requirement.

The [existing Accessibility adapter](evidence/device-startup-ax.json) returned two elements and omitted the page marker. This is a bounded read result. It does not cover direct menu attributes, every text API, or other semantic actions.

The attack runners count only submissions added after each attempt. They require the declared physical completion, independent accepted action, unchanged process, unchanged binary, and device binding. The fixture clears its field after success. A new admitted event without completed action stops further trials to avoid uncertain form state.

```sh
python3 tools/run_device_session.py attack --operator-physical-completion-confirmed
python3 tools/run_device_vision.py --operator-physical-completion-confirmed
```

This result supports the tested keyboard path on this machine. It does not establish an agent-free browser or general browsing compatibility. Pointer input remains disabled. The bootstrap lacks device attestation. The capture-protected flavor needs its own usable physical comparison and attacks. Menu actions, input methods, and binding attacks remain open.

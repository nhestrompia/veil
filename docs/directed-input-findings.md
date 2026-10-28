# Directed keyboard attack calibration

A global click followed by PID-directed typing completed all six control tasks. Both Unicode typing and physical key codes worked after that focus step. The original route that directs every event still failed its controls.

| Route | Control completion | Interpretation |
| --- | --- | --- |
| Global click, PID Unicode keys | 3/3 | Working mixed attack |
| Global click, PID physical key codes | 3/3 | Working mixed attack |
| All-directed original events | 0/3 | Inconclusive adapter |
| All-directed annotated window and key codes | 0/3 | Inconclusive adapter |

The annotated variant uses a window identifier owned by the research PID. It adds public window-routing fields, single-click state, and a matching mouse-event number. These annotations did not complete the control task. They do not establish a defensive block.

The working mixed route isolates click focusing from directed keyboard delivery. It does not prove that a fully directed mouse click works. The [diagnosis](research/directed-input.md) explains the earlier event traces and API contracts. The [expanded controls](evidence/directed-input-controls.json) preserve every trial and the final probe hash.

Across eleven routes and three repetitions, 27 control tasks completed. The original and annotated all-directed routes account for all six inconclusive results. The final probe uses its existing approved Accessibility, event-posting, and Screen Recording grants. No new permission scope belongs to this calibration.

The revised keyboard browser still needs a physical navigation control and same-session attacks with these calibrated adapters. A positive control alone supplies no prevention result.

```sh
python3 tools/run_native.py --targets InspectableControl --routes pid-keys-hid pid-keys-keycodes-hid pid-window-keycodes-hid --repetitions 3 --output artifacts/directed-controls
```

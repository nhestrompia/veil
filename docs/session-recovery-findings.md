# Native session recovery and external drag entry

Research date: 2026-10-24. Native UI access works again. The final probe reports effective Accessibility, event-posting, and Screen Recording grants. The registry no longer supplies its lock flag, so that observation remains unknown. Working controls establish the available routes.

System Settings initially showed enabled entries while the rebuilt probe reported false grants. Removing and adding the same approved app restored effective access. No TCC database edit or new permission scope was necessary. The fixture server also stopped overnight. It now runs again with temporary sleep prevention during these experiments.

## Working controls

The external Accessibility adapter completed a reference website trial. A separate computer-use client entered the fixed fake text and completed a server-recorded action. Window-scoped capture and OCR also worked during the drag experiments. These results replace the earlier unavailable-UI and permission-preflight observations for this build.

Ordinary generated input still needs calibration. Nine CGEvent control trials failed to complete the reference task despite true permission checks. They cover source states, directed keyboard variants, and three insertion points. These failures are inconclusive. They establish neither browser resistance nor a working mouse adapter.

The adapter now records the insertion point separately from source state. The older session, HID, and private labels selected source states but all used HID insertion. Core Graphics exposes separate insertion points. [Apple posting API](https://developer.apple.com/documentation/coregraphics/cgevent/post(tap:)), [Apple insertion points](https://developer.apple.com/documentation/coregraphics/cgeventtaplocation)

## An independent AppKit attack works

The source app creates its window after AppKit finishes launching. It now uses a standard titled window, which the computer-use tool can observe and operate. It records the real drag-session callback separately from API return. Its fixed pasteboard item still contains only `native-input`. It never accesses the general clipboard.

A computer-use drag reached normal page drag-entry callbacks. A separate fixture mode records one action when the page receives its first drag entry. This models an early page action. It does not require text import, a completed drop, or a Return key. The input-field-only pilot and full text-drop attempts remain inconclusive.

An attacker-owned source can also start that AppKit session with a constructed event. The successful automated route posts no OS mouse or keyboard events. The source process remains separate from the browser. No browser code injection or automation bridge takes part.

## Ten fresh paired sessions

| Route | Reference actions | New candidate actions | Candidate drag events | Explicit refusals |
| --- | --- | --- | --- | --- |
| AppKit source session | 10/10 | 0/10 | 0/10 | 10/10 |
| Computer-use pilot | 1/1 | 0/1 | 0/1 | 1/1 |

Each candidate first completes exactly one private diagnostic action. The controller checks that independent baseline before it starts the external source. It counts only later submissions. Every tested candidate refused `web.entered` and `web.updated`. No external trial admitted an authorized keyboard event.

The automated pairs use fresh processes, the same source binary, and the same probe binary. Both browser conditions use normal window levels. The [saved evidence](evidence/session-recovery-results.json) separates the automated matrix, computer-use pilot, and failed CGEvent controls. Unused elevated-window variants were removed after diagnosis.

The candidate is a separate diagnostic build of the keyboard browser. Its private startup supplies a loaded page without a new physical test. The measured boundary is external drag entry into that prepared browser. This is not a new physical usability control, release-startup result, or proof of full text-drop prevention.

## Commands and remaining limits

```sh
bash scripts/build-probe.sh
bash scripts/build-drag-source.sh
bash scripts/diagnose-browser-keyboard.sh --build-only
python3 tools/run_drag_delivery.py --entry-action --source-session-only --repetitions 10 --output artifacts/source-session-final
```

`prepare_cua_drag.py` supplies image coordinates and independent scoring for the computer-use route. It creates no input endpoint in the browser. Fifteen Python checks pass, and the Swift apps compile with warnings as errors. The deliberate legacy C API warning remains separate.

The current grants and UI blocker are resolved. Future ad hoc rebuilds still require effective-grant checks. CGEvent calibration, complete text drops, capture-restricted physical visibility, and the broader acceptance matrix remain open. The project still does not meet the agent-free gate.

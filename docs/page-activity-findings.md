# Page-side activity readback

The optional fixture observer records changes in document.hasFocus() and document.visibilityState. It posts only state names and page-local timestamps. It does not record field text or send a task action. The controller saves activity history before, during, and after the external cycle.

One ordinary password comparison calibrated this readback. The candidate reported hidden state while away, then visible/unfocused and visible/focused states after return. It also reproduced one external focus action. The helper posted no input during the cycle. The application admitted zero keyboard events.

The candidate released its WebKit ownership flag while hidden and restored it after return. The private resumed task passed. All temporary cleanup passed, and aggregate Secure Input was off afterward.

The fixture performs two startup navigations in this diagnostic. Their initial observations share one trial. Duplicate initial entries do not establish separate native focus changes. Compare cycle snapshots after the baseline.

This is a system-engine calibration. No positive custom-engine identity or protected-state result exists yet. Future comparisons must test both native and stable modes in the same custom engine.

See [saved evidence](evidence/page-activity-results.json).

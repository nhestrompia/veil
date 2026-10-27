# Live capture-filter refresh comparison

Milestone 127 uses the approved Screen Recording grant for the unchanged CaptureRefreshProbe. The request initially returns false, and the user reports that the app is absent from Settings. The user then adds the exact app and reports access. A fresh LaunchServices preflight confirms effective access.

The live comparison uses the exact archived executables from milestone 125. The restricted image is the one the user reports as physically visible. Strict bundle signature checks pass without re-signing either image. The helper's executable and source retain their permission-manifest hashes.

| Stream stage | Clear reference before | Restricted window | Clear reference after |
| --- | --- | --- | --- |
| Initial window inclusion filter | Marker recovered | No complete frames | Marker recovered |
| Updated owned-app inclusion filter | Marker recovered | No complete frames | Marker recovered |
| Updated window inclusion filter | Marker recovered | No complete frames | Marker recovered |

The restricted stream starts, accepts both filter updates, and stops without error. The receiver observes no complete frames or frame-status values during the three two-second stages. It does not count all callbacks. No restricted page marker is recovered. This differs from a captured black image. The result remains inconclusive for frame-content exclusion because there are no candidate frames to inspect. Both clear controls show that the granted helper can capture the reference before and after this trial.

The final clear reference runs separately after the runner stops on the restricted window's missing frames. The final runner now preserves that missing-frame result while completing the after-reference. It still stops on a failed reference or unverified stream cleanup. No second restricted trial runs.

## Calibration corrections

The first pilot stops on a scorer error. Its clear frames are readable, but Vision substitutes Cyrillic-shaped glyphs in the fixed hexadecimal marker. The scorer now recognizes the observed Cyrillic O and Ze as zero and three. It retains the raw exact-match result. Three regression checks cover the recorded readable marker, a different marker, and an empty black-frame result. Rescoring the pilot recovers its marker in all 24 saved frames. The original failed score remains in the artifacts.

The second pilot stops before launching its candidate. Its rebuilt restricted executable differs from the recorded physical-test hash. The final comparison restores each archived executable and checks its original bundle signature. This preserves the exact physical baseline without asking the user to repeat it. The helper remains unchanged throughout.

## Scope

This probe tests one stream with owned-window and owned-app inclusion filters. It does not reproduce the unfiltered-display configuration in the [Apple forum report](https://developer.apple.com/forums/thread/808016). No broader screenshot guarantee follows. QuickTime capture, unfiltered compositor capture, resizing, fullscreen transitions, and longer recordings remain open. The probe saves at most eight sampled complete frames in each stage. Missing candidate frames do not count as a general blocking result.

The fixed local page completes one process-local keyboard task in each host. No device reader, synthetic system input, audio capture, administrator access, or unrelated app capture occurs. That task is a functionality check, not a physical input baseline or an external action defense.

See [saved live results](evidence/capture-refresh-live-results.json). All owned hosts and fixture servers stop. Independent process checks verify cleanup. All seven earlier permissioned images and the new granted helper retain their hashes. Agent-free browsing remains unproven.

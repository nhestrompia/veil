# Foreground input and exposure experiments

Status: both variants compile and pass signature checks. Live prevention results remain pending. The [route calibration](route-calibration.md) supersedes the initial hard console preflight.

`SecureInputExperiment.app` enables Secure Event Input while active and releases its own request before deactivation or termination. The log records the API result. This tests injection while the mode is active. It does not establish a suitable policy for general browsing. Apple documents this API for sensitive entry and warns against general text use. See the [remaining-boundary research](research/remaining-boundaries.md).

`ReducedExposureExperiment.app` adds `WKWebView.setAccessibilityHidden(true)` and `NSWindow.sharingType = .none` to that experiment. This intentionally removes accessibility support for the page. Neither property establishes agent-free operation. The sharing flag already lacks a current capture guarantee. The combined variant measures what these settings actually change.

## Test status

The first rerun failed its baseline controls. ScreenCaptureKit returned error `-3811`, and system capture failed. The AX traversal encountered application cycles before it reached page controls. No result from that run counts as prevention.

Both the registry and `CGSessionCopyCurrentDictionary` then reported that the current console session was locked. The user reported that the Mac should be unlocked. This disagreement remains an environment issue, not a browser defense.

The initial runners refused reported locks or unknown console states. That rule was too broad because later native controls worked despite the recorded flag. The runners now save console metadata as advisory context. Explicit defensive refusals need matched working action controls. All ten Python tests pass. The AX probe now deduplicates elements and skips system menus to avoid cycles and unrelated recent-document entries.

The updated probe is built and signed. Its approved grants are effective after registration refresh. A future rebuild still needs an effective-permission check.

## Repeat the experiments

Use a native session with working control routes. Start the fixture before the runners.

```sh
bash scripts/build.sh
bash scripts/build-probe.sh
python3 tools/run_native.py --targets AgentFreeBrowser SecureInputExperiment --routes hid keycodes-hid --repetitions 3 --output artifacts/foreground-native
python3 tools/run_capture.py --targets AgentFreeBrowser SecureInputExperiment ReducedExposureExperiment --repetitions 3 --output artifacts/foreground-vision
```

The reduced-exposure build needs screenshot-based attacks because missing AX controls would prevent the AX-based adapter from finding coordinates. A failed coordinate adapter never counts as a blocked action. A usable positive control and explicit effective-mode logs are prerequisites for a prevention claim.

# Offline mouse replay pilot

The saved user-declared physical session contains 490 application pointer records. A new offline tool extracts motion features from that session and fifteen saved synthetic sessions. It collects no new input and sends no event to the desktop.

The physical declaration remains separate from the measurements. The sample has no accepted fake action and no raw pointer callbacks. Its instrumentation keeps `humanBaselineVerified=false`. It cannot establish a usable human task or a general human distribution.

## Replay limit

The tool removes absolute coordinates, absolute start time, source-state fields, process IDs, and class labels from its motion input. It computes duration, path length, displacement, path ratio, speed statistics, turn angles, and the largest sample gap.

An offline copy of the same trajectory produces exactly the same feature vector. A classifier that receives only those features therefore cannot distinguish that copy. This is a property of the selected features and saved trace. It is not a live macOS replay attack or a completed website action.

This result rules out treating these behavior features alone as a proof of human origin. It does not measure evasion against a deployed detector, a fresh challenge, or a different task layout. The browser does not enable a behavior classifier from this pilot.

## Dataset limits

All fifteen synthetic sessions remain in the report. Samples without at least three pointer records keep an explicit unavailable result. They do not disappear from the comparison. Keyboard and raw device records do not enter the motion features.

There is one declared physical session. No training split, classifier accuracy, human false-block estimate, or adaptive live success rate follows. The synthetic recordings also differ in event sampling and task completion from the physical recording. Those differences can expose collection artifacts instead of human behavior.

The [offline evidence](evidence/behavior-replay-results.json) saves input hashes and aggregate features. It exports no raw trace or absolute pointer location. Four checks cover metadata exclusion, translated coordinates, invalid timing, keyboard exclusion, and copied behavior. All 36 Python checks pass.

The next behavioral experiment needs several physical users and devices, successful tasks, independent replay traces, and adaptive evaluation on fresh layouts. The [experiment plan](research/mouse-behavior-experiment.md) retains those requirements. Agent-free status remains unproven.

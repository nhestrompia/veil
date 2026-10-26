## Milestone 82: timer-gap calibration

The new local fixture arms one timer action after the private startup task. A gap above 500 milliseconds triggers that action once. The controller requires exactly one startup action, then a three-second stationary period without another action. Only then does it hide and restore the app for three seconds. It posts no external input.

The first native-engine run already contained two accepted actions before the stationary period. A timer gap of 516 milliseconds occurred before the attack. Its later hide cycle recorded no action. That sequence cannot calibrate a timing attack. The controller now rejects an early action instead of accepting that sequence as a valid stationary control.

No stable comparison follows without a valid native control. This experiment does not show that timing behavior is protected. All 111 Python checks pass. The physical browser and permissioned probes remain unchanged.

The fresh guarded run also contained two initial actions. It returned inconclusive before hiding the app. Both temporary processes passed cleanup, and Secure Event Input returned to off.


## Milestone 83: active-page timer bypass

A small animation keeps the foreground fixture active. This distinguishes the experiment from the static page that triggered before the attack. Both native and stable modes began with exactly one startup action. Both passed three stationary seconds without a new action or admitted key.

Hiding each app for three seconds triggered one accepted website action. Native mode recorded a timer gap of 1,001 milliseconds. Stable mode recorded 830 milliseconds. Both activation cycles admitted zero input events. No external input or candidate Accessibility action was sent.

The stable page continued to report visible and focused state. The retained visual-idle flag controls timer alignment independently in the pinned source. This identifies the next hypothesis for a bounded patch. It does not yet prove that changing that flag closes the route.

Every temporary process passed cleanup, and Secure Event Input returned to off. The evidence includes engine receipts and framework hashes. Agent-free operation remains unmet.


## Milestone 85: adaptive timer controls and desktop prerequisite

The first readiness check required ten intervals below 200 milliseconds. Its native control never reached that condition. The controller skipped the stable comparison and cleaned up both research processes.

The adaptive variant measures ten baseline intervals. Its action threshold is the greater of 500 milliseconds or the observed maximum plus 250 milliseconds. The page records its threshold before the stationary control. The controller then requires three unchanged seconds and performs an eight-second hide cycle.

The native trial measured a maximum interval of 1,000 milliseconds and chose a 1,250-millisecond threshold. Its stationary control passed. No timer action followed. Hide succeeded, but return activation failed. The result is inconclusive, and stable mode was skipped.

macOS also reported the console locked. That flag remains advisory. The failed activation receipt independently prevents a valid negative comparison. All 112 Python checks pass. Temporary process cleanup passed, and Secure Event Input returned to off. The revised engine remains compiled, with its runtime repair unverified.

A desktop-unlock request is pending. Resume with the adaptive timer comparison after foreground controls work. Then run the password ownership control and the broader editor/input matrix. Keep the frozen physical browser and permissioned probes unchanged.


## Milestone 86: unlocked timer comparison

Three fresh native/stable comparisons passed their stationary controls. Each native mode completed one timer-triggered action after hiding. Native gaps measured 1,000, 1,000, and 1,079 milliseconds. Each stable mode recorded no timer action during the same eight-second hide cycle.

All six activation cycles admitted zero input events. UI and content framework identities passed in every trial. Every temporary process passed cleanup. Secure Event Input returned to off after every comparison. The frozen physical browser and probes remain unchanged.

These results support the revised projection for the measured adaptive timer route. They do not establish every timing signal or website as agent-free. Native ownership, independent element focus, and additional external actions remain separate checks.

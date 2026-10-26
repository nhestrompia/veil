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

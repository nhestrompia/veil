## Milestone 82: timer-gap calibration

The new local fixture arms one timer action after the private startup task. A gap above 500 milliseconds triggers that action once. The controller requires exactly one startup action, then a three-second stationary period without another action. Only then does it hide and restore the app for three seconds. It posts no external input.

The first native-engine run already contained two accepted actions before the stationary period. A timer gap of 516 milliseconds occurred before the attack. Its later hide cycle recorded no action. That sequence cannot calibrate a timing attack. The controller now rejects an early action instead of accepting that sequence as a valid stationary control.

No stable comparison follows without a valid native control. This experiment does not show that timing behavior is protected. All 111 Python checks pass. The physical browser and permissioned probes remain unchanged.

The fresh guarded run also contained two initial actions. It returned inconclusive before hiding the app. Both temporary processes passed cleanup, and Secure Event Input returned to off.

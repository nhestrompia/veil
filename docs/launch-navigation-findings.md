# Startup navigation requires physical submission

The keyboard browser originally loaded launch URLs without input. The agent reached its fresh loopback endpoint in all three trials. The revised build only fills the address field. It waits for physical submission before navigation.

| Build | Unattended document requests | Matched control requests |
| --- | --- | --- |
| Earlier keyboard experiment | 3/3 | 3/3 |
| Physical-submit startup | 0/3 | 3/3 |

Each trial creates a fresh loopback endpoint and starts one browser process. The separate server counts requests to that exact path. The controller never requests the page itself. The test waits 2.5 seconds after browser readiness before closing that research process.

The revised trials record an effective device grant and a successfully opened reader. They also record the pending-address state and no device binding. A prior run without the effective grant remains a calibration failure. The saved final comparison uses the working reader.

The [earlier results](evidence/launch-before.json) prove that the launch route bypassed the first keyboard experiment. The [revised results](evidence/launch-after.json) cover this unattended launch route only. They do not establish human navigation or general agent prevention on the revised binary.

The experimental keyboard browser now focuses the address field at startup. The user binds a keyboard with Space, then submits the address with Return. Command-L selects the address for later manual navigation. The separate control builds keep their automatic research startup behavior.

The earlier physical task and twenty stopped input trials belong to the earlier binary. The revised browser needs a new physical control and same-session attacks. It still has no pointer support or authenticated device bootstrap. The agent-free claim remains unmet.

```sh
bash scripts/build.sh devicekeyboard
python3 tools/run_launch_navigation.py --repetitions 3 --output artifacts/launch-after
```

The first subsequent physical trial failed. The user reported a black whole window. The [visibility diagnosis](startup-visibility-diagnosis.md) records the controls and the later hidden-app finding. No usable startup-protection claim follows from this failed physical trial.


The user later confirmed address-bar visibility after selecting the app. A separate repeated-Space bug then replaced the selected address. The revised startup dispatcher consumes repeated binding Spaces until navigation begins. Its native regression and the remaining physical check are recorded in the visibility diagnosis.

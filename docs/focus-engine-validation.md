# Validate the new focus browser

This runbook repeats the focus attack after a physical task in the new browser identity. The current image and engine are pinned in the [manifest](evidence/focus-engine-browser-manifest.json). Milestone 153 records approved and effective Input Monitoring. Do not request or reset it again. Use the permission query to confirm access.

## Run diagnostic comparisons

From the project root, run the suite with a fresh output directory:

```sh
PYTHONPATH=tools python3 tools/run_focus_engine_regression.py \
	--output artifacts/NEW-FOCUS-COMPARISON
```

The command runs only the owned diagnostic apps and loopback fixture. It uses no system input posting or new macOS grant. Require `diagnostic-regression-passed` and verified cleanup. Owner-generated typing does not count as a physical control.

The builder refuses replacement after any recorded permission approval or request. Before consent, `--replace-ungranted` preserves the previous images in a build backup. No granted image can use that rebuild path.

## Establish the physical control

The following grant procedure is historical. The current image already has approval and effective access.

1. Obtain explicit approval for a new identity before its Input Monitoring request.
2. Record that approval in the manifest.
3. Run the guarded request with a fresh log path:

```sh
PYTHONPATH=tools python3 tools/launch_focus_browser.py \
	--request-permissions --log artifacts/NEW-INPUT-REQUEST.log
```

4. Complete any required macOS consent directly on the Mac.
5. Query effective access:

```sh
PYTHONPATH=tools python3 tools/launch_focus_browser.py \
	--permissions --log artifacts/NEW-INPUT-PREFLIGHT.log
```

6. Record effective access only after the preflight reports `permission=true`.
7. Start one physical session with a fresh output directory:

```sh
PYTHONPATH=tools python3 tools/run_preview_session.py --engine \
	--surface focus-action --output artifacts/NEW-PHYSICAL-SESSION
```

The session owns one browser and a private fixture. Its stop file and one-hour watchdog close both. The startup address requires physical Space, then Return. Use physical Tab to reach the page field. Type only `native-input`, then Return. Require a visible page, device binding, exactly one accepted action, and the user's confirmation.

Save the separate physical declaration with that session's exact PID and executable hash. Use the existing `operatorDeclaresPhysicalCompletion`, `deviceBound`, and `acceptedSubmissions` fields. This declaration records the user report. It does not independently attest hardware origin.

## Repeat the external attack

Use the fresh session and declaration with the recorded native control:

```sh
PYTHONPATH=tools python3 tools/run_focus_browser_attack.py \
	--session artifacts/NEW-PHYSICAL-SESSION/session.json \
	--physical-control artifacts/NEW-PHYSICAL-CONTROL.json \
	--control artifacts/focus-engine-152/accepted-suite/native-focus/results.json \
	--output artifacts/NEW-PHYSICAL-ATTACK
```

The operator must leave the browser untouched during the attack. The helper activates only pinned research apps. A new accepted action is a bypass. Three completed zero-action cycles support only the measured focus result. Missing controls or mixed input make the result inconclusive.

After preserving the oracle and logs, create the session's `stop` file. Require `ownedHostStopped=true` and `ownedFixtureStopped=true`. Update the findings with the exact new process and image. Do not replace the earlier vulnerable-build evidence.

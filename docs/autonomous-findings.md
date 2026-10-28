# Autonomous bootstrap and browser controls

The user requested continued research without further physical tasks. The new experiments therefore separate software attack outcomes from an internal browser-functionality control. They do not replace the earlier physical evidence or establish usability on the revised release binary.

## Software bootstrap attacks

Five adapters sent Space, Return, Tab, the fixed fake token, and Return. The adapters used session, HID-state, private-state, legacy HID posting, and HID-manager report posting. Each route ran three times against a fresh control and a fresh keyboard-browser process.

All fifteen controls completed the independent website action. None of the fifteen candidate trials bound a keyboard, admitted an input event, or completed a website action. The reader opened successfully in every candidate trial. The gate recorded 495 refusals. Both HID-posting variants returned successful posting codes.

The [matrix](evidence/bootstrap-results.json) records these observations as `bootstrap-not-observed`. That label does not mean usable protection or authenticated hardware. Physical input absence was not independently verified. The earlier pilot contains one additional paired attempt per route.

```sh
python3 tools/run_bootstrap_attacks.py --repetitions 3
```

## Internal browser functionality

A diagnostic copy of the browser creates private authorized events inside its own process. It preserves the production application dispatcher, address workflow, menu policy, and WebKit path. It replaces device-reader startup with the fixed internal sequence. The normal browser build contains no switch that enables this sequence.

The control preserves the address across repeated startup Spaces, opens it with Return, focuses it with Command-L, reloads, and completes the HTML form. The independent fixture accepted one action in each run. The host has a separate diagnostic identity and requests no Input Monitoring grant. These are internal functionality results, not external bypasses or physical controls.

## Direct Accessibility and capture reads

The external adapter queries the main window, focused window, application focus, system focus, and two hit-test points inside the owned window. It discards roots and descriptions from other process IDs. Apple documents that system-wide hit testing can return objects from any app, which makes this ownership check necessary. [Apple hit-test API](https://developer.apple.com/documentation/applicationservices/1462077-axuielementcopyelementatposition), [Apple process-ID API](https://developer.apple.com/documentation/applicationservices/1460337-axuielementgetpid)

The [readable reference](evidence/direct-ax-control.json) exposed its fresh marker and returned 32 elements. The [visible diagnostic](evidence/internal-keyboard-visible.json) and [restricted diagnostic](evidence/internal-keyboard-restricted.json) each returned two elements without the marker. Each flavor completed its internal form action before the read. These are single-run, bounded read comparisons.

Window-scoped capture recovered the marker from the sharing-enabled diagnostic. The restricted diagnostic produced a black image without the marker. This describes the tested capture route. It does not verify the physical display or other screenshot routes. The diagnostic event source and binary differ from the release browser.

```sh
bash scripts/diagnose-browser-keyboard.sh --build-only
python3 tools/run_internal_keyboard_control.py --external-reads --output artifacts/internal-keyboard-visible
bash scripts/diagnose-browser-keyboard.sh --capture-restricted --build-only
python3 tools/run_internal_keyboard_control.py --external-reads --output artifacts/internal-keyboard-restricted
```

The fixture now records only accepted/rejected outcomes for submissions. It no longer retains submitted text. Event telemetry still omits typed values and key codes.

The browser remains a research prototype. Pointer input, authenticated device bootstrap, physical usability of the revised build, complete semantic coverage, and the stronger agent-free goal remain unverified.

# Direct menu actions bypass the event gate

A direct Accessibility query recovered the keyboard browser's File and Edit menus. The existing page traversal omitted menu bars, so its earlier hidden-page result did not cover this route. The separately queried menus exposed Open Location, Paste, Select All, and system-added text commands.

The external probe invoked Open Location successfully. A window-scoped image showed the address selected afterward. The gate recorded no admitted input events. This establishes a semantic browser-focus action outside the gate. It does not establish a new website submission or arbitrary text insertion. See the [action record](evidence/menu-semantic-action.json) and [resulting window](evidence/menu-open-location.png).

The probe reads only the research app's File and Edit branches. It does not traverse Apple menus, recent documents, or other apps. A proposed paste experiment never ran. Automatic approval review rejected its temporary access to the existing system clipboard. The replacement probe has no clipboard access.

## Failed getter experiment

Apple documents the application menu-bar accessibility getter and selector-access policy. The experiment added an explicit nil getter while the existing selector policy already returned false. The external query still recovered Edit commands. The [paired result](evidence/menu-getter-failure.json) records this failed candidate. The production code removes that ineffective getter. [Apple accessibility protocol](https://developer.apple.com/documentation/AppKit/NSAccessibilityProtocol), [Apple menu-bar accessor](https://developer.apple.com/documentation/appkit/nsaccessibilityprotocol/setaccessibilitymenubar%28_%3A%29)

## Remove content menus from the experiment

The keyboard experiment now omits File and Edit menus. Its app menu retains Quit. Physical Command-L invokes address focus only after the event gate consumes an exact authorized event. Ambient and replayed shortcut events fail the dispatch check. Other browser variants retain their existing menus.

The [paired menu check](evidence/menu-boundary-fixed.json) still finds Edit commands in the unchanged inspection control. It finds no File/Edit content commands in the revised keyboard experiment. The menu bar itself remains present. This is a bounded interface result, not universal semantic-action prevention.

```sh
python3 tools/run_menu_boundary.py
bash scripts/test-device-queue.sh
```

The revised keyboard binary needs its own physical control and attacks. Earlier native and vision refusals belong to the previous binary. Capture protection, text-system APIs, contextual menus, bootstrap attacks, and general browsing compatibility remain separate questions.


The capture-restricted flavor repeated the [paired menu result](evidence/menu-boundary-protected.json). Its [launch comparison](evidence/launch-menu-fixed.json) made zero unattended requests in three trials, with three working controls and effective device access. Physical usability remains unverified for this exact binary. The user requested autonomous continuation, so no further physical task was collected.

The session runner now rejects controls from a different probe binary before any input attempt. The menu adapter changed the probe signature, so the next input matrix requires fresh controls. Earlier recorded refusals used their matching probe binary and remain separate evidence.

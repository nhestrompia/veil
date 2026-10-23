# Isolated compositor capture

A compositor test can reveal other apps underneath a capture-excluded window. The revised adapter therefore requires a controlled research backdrop. The old unrestricted compositor command now refuses capture. The ordinary vision runner uses only window-scoped routes.

The diagnostic host places an opaque owned backdrop behind its target window. Both windows temporarily sit above ordinary app windows. The adapter accepts their explicit window IDs only for the internal diagnostic bundle. It verifies ownership, opacity, ordering, coverage, foreground state, and intersecting overlays before capture. It repeats those checks before writing an image.

The display filter remains unfiltered. Its source rectangle lies inside the verified research coverage. This tests the compositor path while the backdrop covers unrelated content underneath. The high window levels belong only to this diagnostic. They are not a browser feature or an input defense.

## Paired result

| Diagnostic flavor | Internal form completed | Page marker in compositor image | Owned backdrop recovered |
| --- | --- | --- | --- |
| Sharing enabled | Yes | Yes | No |
| Sharing restricted | Yes | No | Yes |

The [readable control](evidence/compositor-visible.json) and [restricted run](evidence/compositor-restricted.json) each completed a real WebKit form through private internal events. Both coverage checks passed. The readable image exposed its fresh marker. The restricted image instead showed the [controlled backdrop](evidence/compositor-backdrop.png). Each flavor ran once.

This is a bounded compositor observation. It does not establish physical visibility, general screenshot prevention, or an agent-free release browser. The host uses a diagnostic binary and an internal event source. Continuous ScreenCaptureKit streams and other capture methods remain separate tests.

## Coverage failure control

A third diagnostic used a backdrop measuring only 40 by 40 points. The [guard result](evidence/compositor-invalid-backdrop.json) reports insufficient coverage. No compositor image file was created. The internal form still completed before this refused capture.

```sh
bash scripts/diagnose-browser-keyboard.sh --backdrop --build-only
python3 tools/run_internal_keyboard_control.py --external-reads --output artifacts/compositor-visible
bash scripts/diagnose-browser-keyboard.sh --backdrop --capture-restricted --build-only
python3 tools/run_internal_keyboard_control.py --external-reads --output artifacts/compositor-restricted
bash scripts/diagnose-browser-keyboard.sh --invalid-backdrop --build-only
python3 tools/run_internal_keyboard_control.py --external-reads --output artifacts/compositor-invalid-backdrop
```

The separate protected-video experiments still failed their earlier physical visibility controls. These new window-sharing results do not change those findings.

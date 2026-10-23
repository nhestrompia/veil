# Continuous screen-stream comparison

The new adapter uses SCStream rather than the screenshot manager. It registers only a screen output and disables audio. It accepts the first frame with complete status, copies that frame into an immutable image, and stops the stream. A four-second wait limit rejects missing completed frames. The receiver shares its image and status values under a lock.

Apple describes stream outputs and frame-status metadata separately from screenshot capture. The adapter follows that distinction. It does not treat an idle, blank, or merely started frame as usable video. [Apple capture sample](https://developer.apple.com/documentation/screencapturekit/capturing-screen-content-in-macos), [Apple frame status](https://developer.apple.com/documentation/screencapturekit/scframestatus)

## Six fresh runs

| Diagnostic flavor | Completed internal forms | Fresh markers recovered | Owned backdrop recovered |
| --- | --- | --- | --- |
| Sharing enabled | 3/3 | 3/3 | 0/3 |
| Sharing restricted | 3/3 | 0/3 | 3/3 |

The [results](evidence/stream-capture-results.json) record fresh processes, random markers, binary hashes, and verified backdrop coverage before and after capture. Every returned image came from a completed stream frame. All six runs used the same external probe binary.

The stream uses the same isolated display crop as the [compositor experiment](isolated-compositor-findings.md). It refuses capture without two distinct owned windows and complete opaque coverage. The diagnostic host temporarily covers unrelated windows with its research backdrop.

These results cover the first completed frame in each stream. They do not establish long-duration behavior, resizing, fullscreen, physical visibility, or general agent prevention. The internal form sequence is a functionality control, not physical input.

## Helper cleanup

The native probe now records its process ID before it starts work. The controller removes stale records before launch. If its forty-second launch wait expires, it checks the recorded process path and stops only that research helper before returning the timeout. It checks identity again before a final forced stop.

Five lifecycle checks cover timeout propagation, valid helper shutdown, invalid records, unrelated processes, and a reused process ID. All fifteen Python checks pass. These tests exercise the controller's failure path with mocked process results. The live capture runs complete normally.

```sh
bash scripts/diagnose-browser-keyboard.sh --backdrop --build-only
python3 tools/run_internal_keyboard_control.py --external-reads --stream --output artifacts/stream-visible
bash scripts/diagnose-browser-keyboard.sh --backdrop --capture-restricted --build-only
python3 tools/run_internal_keyboard_control.py --external-reads --stream --output artifacts/stream-restricted
```

The stronger agent-free goal remains unmet. The revised release binary still lacks a new physical usability control and complete coverage of inspector, semantic, and device-origin attacks.

# Bounded renderer token experiment

The renderer helper now supports a bounded remote-token scan. It retains exact research ownership checks and the loopback-only action contract. A token scan can test elements absent from an ordinary application-root tree.

## Method and limits

The test constructs the twenty-byte token layout used by AltTab's [original accessibility wrapper](https://github.com/lwouis/alt-tab-macos/blob/master/src/macos/api-wrappers/AXUIElement.swift). It resolves the private `_AXUIElementCreateWithRemoteToken` symbol at runtime. This is an attack-tool experiment, not a browser dependency or supported API guarantee.

Each renderer scan tries at most 1,024 element IDs from zero and stops after three seconds. The complete query has an eight-second budget and a 500-element traversal limit. It rechecks process identity and responsibility before queries. It discards elements owned by another PID before attribute reads. It installs no input hook and sends no CGEvent.

A host query first initializes accessibility through the ordinary external AX route. Read and action calibration are separate. A read reference must recover its own fresh marker. An action reference must also verify the fixture URL and complete one accepted task. Failed references skip the corresponding candidate route. Candidate absence within this ID range cannot prove that every possible remote token is inaccessible.

The fixed token-layout check covers byte order and rejects system PID values. Fixture URL matching also rejects a trailing newline. All 70 Python checks and the Swift ownership and URL checks pass.

## Runtime result

The user approved the same-app refresh sequence. Off/on did not restore access. The app-only reset succeeded. The Add picker remained disabled until System Settings closed and reopened. Exact-bundle Add then restored effective Accessibility. The helper identity remained frozen afterward.

An initial token reference recovered its marker and exposed the fixture field and button. Its URL guard remained unsatisfied, so it sent no write or press. That is a working read reference, not a working action reference.

Three further references each recovered the correct fresh marker. Three matched scans of the unchanged candidate recovered no marker, field, or task button. Every scan covered IDs zero through 1,023. Candidate token roots increased from two to four across the samples, with application, group, scroll-area, and web-area roles. Some returned descendants failed the exact-PID ownership check and were discarded before reads.

Candidate writes were skipped because no action reference completed. No new task submission occurred. Every helper and readable reference passed cleanup. These results concern bounded renderer reads. They do not establish prevention of renderer actions or exclude tokens outside the scanned range.

The [saved evidence](evidence/renderer-token-results.json) retains the initial action-limited reference, the three matched read comparisons, and permission recovery. The frozen helper SHA256 is `00833c1a0cdd31b0b4d49acbd544a44cfa88f26e231fee063810dd9a7927e332`.

The browser and original NativeProbe remained unchanged. Human keystroke observation remains a separate privacy result. No agent-free conclusion follows from an unrun scan or an unavailable reference.

# Embedded-document navigation and repeated page tests

The navigation policy now accepts about:blank and about:srcdoc inside frames. Top-level navigation and the address bar still reject those addresses. Other about pages, encoded variants, query-bearing about URLs, file URLs, data URLs, and JavaScript URLs remain refused.

The action and response delegates use the frame context. Unknown target-frame context follows the top-level restriction. Download and unsupported-response checks still apply. The change restores a real srcdoc task without a website-specific exception.

## Scope of the comparison

A new diagnostic and readable reference contain the policy change. They remained unchanged during the page matrix. The diagnostic uses the same gate and protected configuration, with private authorized typing and frame-focus assistance. It starts no HID reader. This supplies a functional baseline for each editor, not a physical-human control.

The standalone srcdoc comparison completed its private task. Its readable reference completed the external HID task. The candidate refused that matched attack and admitted zero input events.

The complete matrix covers ordinary fields, textareas, editable regions, open and closed shadow DOM, dynamic rendering, same-origin frames, cross-origin frames, and srcdoc. All nine private baselines passed. The 45 external cases produced 27 explicit native blocks and 18 inconclusive results. No new task completed through those routes. Vision found no usable candidate field. Candidate AX targets were unavailable, and the textarea and editable-region AX references failed. Those cases remain inconclusive. Every temporary process passed cleanup.

## Remaining boundary

This compatibility fix does not close lifecycle actions. The independent focus and visibility bypasses remain valid. No activation filter or logical-key override is enabled in this diagnostic. General web compatibility and agent-free operation remain unmet.


All 87 Python checks pass. Swift address, embedded-document, response, and device-dispatch checks pass. Production and device-browser source type-check with warnings as errors at the macOS 14 deployment target. The frozen physical browser and NativeProbe remain unchanged. [Saved evidence](evidence/embedded-document-results.json) includes binary identities and all case outcomes.

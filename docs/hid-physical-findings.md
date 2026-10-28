# Physical-input observation

The user supplied one declared physical-input session. The observer recorded 97 raw keyboard values and no raw pointer values. Application events included 12 key-down events, 12 key-up events, three pointer presses, and pointer movement or drag events.

The file contains 611 records across about 13.4 seconds. Collection stopped without reaching the record limit. The file omits typed text, key codes, keyboard values, and device names. The [saved summary](evidence/hid-physical-summary.json) contains aggregate counts only.

The accepted fake-action count is zero. This sample therefore does not establish successful human completion of the form. It does show that this observer received raw keyboard callbacks during the declared physical session. The [generated controls](hid-generated-findings.md) received no raw keyboard callbacks in fifteen successful synthetic trials.

This comparison supports another keyboard experiment. It cannot support a complete pointer gate. The observer matched Generic Desktop keyboards, mice, and pointers. It did not explicitly match digitizer devices. The test does not identify which pointer device the person used or why callbacks were absent.

No computer-use actions ran during the physical collection. The user's declaration identifies the source, but the instrumentation keeps `humanBaselineVerified` false. No classifier, source attestation, or agent-prevention result follows from this sample.

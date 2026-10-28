# Rebuilt browser grant recovery

The rebuilt source-policy browser now reports effective Input Monitoring access. One explicitly approved reset of its own ListenEvent decision, followed by re-adding the exact bundle, restored access. No other app or service decision reset.

Earlier approved off/on and Add operations did not restore effective access. System Settings showed the entry on, but the process still reported false. That Boolean means not granted. The frozen executable did not record the raw permission enum.

## Identity evidence

The TCC log recorded a grant write with the current code-directory hash. A later check for the same browser examined an older hash and returned status -67050. An explicit code requirement for the current hash passed. The prior requirement failed.

The read-only code probe also found the running research app through Security.framework. Its default dynamic validity check returned success. Associated static signing information and a fresh static-code lookup both described the current hash. Signing-information hashes describe static code. They are not a measurement of a kernel cache.

These observations identify a stale requirement in the failed authorization path. They do not establish which record or cache retained it. An identical signed copy with fresh file identities did not restore access. That negative result prevents blaming in-place executable replacement alone.

The [source review](research/tcc-code-identity.md) separates documented ad hoc identity changes, documented kernel caching, and this unresolved runtime behavior. Apple documents a per-bundle ListenEvent reset. The user approved that exact command and fresh consent before execution.

## Reusable diagnosis

`bash scripts/build-code-identity-probe.sh` builds the read-only helper. It accepts only a running DeviceKeyboardExperiment PID. It reads signing information and code validity. It neither requests input access nor controls another process. An unrelated PID returns exit status 2.

The [recovery evidence](evidence/source-policy-grant-recovery.json) preserves check outcomes, explicit requirement statuses, the unchanged executable hash, and the successful one-app reset. The diagnostic browser loaded no website and passed exact process cleanup.

No global TCC reset, system-service restart, database edit, driver installation, or new permission scope occurred. This milestone restores a test prerequisite. It supplies no input-prevention or human-usability result.

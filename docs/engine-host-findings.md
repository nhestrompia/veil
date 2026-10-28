# Host deployment target and stable source staging

The seventh full build failed with exit code 65. CredentialUpdaterShim.swift uses APIs available from macOS 26.2, but the deployment target was 26.0. This is a confirmed compiler failure, separate from the earlier cosmetic quiet-log messages.

The build now takes its deployment target from the host's macOS version. This Mac reports 26.6. The eighth build is active with that target, normal logging, and upstream cache defaults. This personal proof of concept does not claim support for older macOS versions.

Source staging also rewrote already-correct files on every run. That changed timestamps and could schedule unnecessary recompilation. It now skips byte-identical files. All source checks still occur before writes.

The timestamp regression failed before the change and passed afterward. It covers a partial old/new application, exact convergence, and preservation on the second call. All 102 Python checks pass. The running engine build began before this staging optimization, so its current compiler inputs remain unchanged.

A complete engine, loaded-framework identities, and native-versus-stable runtime comparisons remain pending.

See [saved evidence](evidence/engine-host-results.json).

# Renderer filesystem controls

Milestone 102 adds three separate disposable apps. The reference has no App Sandbox entitlement. The minimal sandbox has only App Sandbox. The network-enabled sandbox also has outgoing-network capability. Every app uses the same fixed inline fixture and bounded stdout transport. None loads an external URL or requests an operating-system grant.

The reference appends a fixed marker to a disposable file outside its container. The controller creates that file with mode 0600 and checks its bytes afterward. The native code rejects symlinks, wrong ownership, and unexpected contents before any write. The sandbox comparison uses the exact absolute path to the same kind of file.

Three fresh reference/network-sandbox pairs pass. Every reference appends its marker. Every sandbox open returns EPERM and leaves its file unchanged. All six apps create, write, read, and remove their own temporary canary. JavaScript, snapshot pixels, stable role identities, and process cleanup also pass. A separate pilot pair passes the same checks.

The minimal sandbox blocks the absolute workspace write and passes its temporary-file control, but WebKit fails to launch its services. Direct execution and LaunchServices both show this failure. No valid snapshot results from those trials. The installed framework reports content termination and role PID zero.

Pinned WebKit checks sandboxed clients for outgoing-network permission or access to a networking service. Its comments identify local-resource support without that access as unfinished. This source is consistent with the measured failure. The distinct network-enabled variant succeeds, but that does not prove the installed framework took the exact pinned branch. See [the source review](research/renderer-filesystem-containment.md).

Earlier pilots exposed two measurement errors. Direct execution inherits a responsibility PID that differs from the host PID. Responsibility therefore does not prove exclusive ownership here. App Sandbox also changes the working directory to its container. A relative canary path returned ENOENT and supplied no denial evidence. The final controls use owner-side role getters, kernel records, and absolute canary paths.

A separate read-only helper checks exact research-host and WebKit executable paths before returning credentials. It samples each identity twice while the app remains alive. Every successful role uses real, effective, and saved user ID 501. Native and external records remain available separately. The helper accepts no command and sends no signal.

Five bounded-reader tests and four metadata-refusal tests pass. Both Swift build modes compile with warnings as errors. The C helper also compiles with warnings as errors. The final apps retain hardened runtime signatures. Frozen browser and permissioned probe hashes match.

App Sandbox creates OS-managed app containers and permits writes there. Those research containers remain as application data. Each app removes its temporary-file control. Workspace canaries remain in the saved trial directories. All measured host/service PIDs exit. This experiment does not audit every framework write or establish identical service sandbox rules.

The known same-user pause bypass remains open. No administrator command ran. Cross-user rendering, inherited session capabilities, shared nobody state, and auxiliary cleanup still need a separate reviewed proposal. The completed milestone 98 approval cannot authorize that future test.

Run `bash scripts/build-renderer-filesystem-control.sh`, then `python3 tools/run_renderer_filesystem_control.py --sandbox-kind NetworkSandbox --out artifacts/renderer-filesystem-new`. The output directory must not exist. The controller stops at the first inconclusive comparison.

See [measured results](evidence/renderer-filesystem-results.json). Agent-free operation remains unmet.

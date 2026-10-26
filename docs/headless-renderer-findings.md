# Headless renderer findings

Milestone 99 establishes a same-user rendering baseline. A separate hardened diagnostic loads one fixed inline fixture in a nonpersistent WKWebView. It creates no window, posts no input, requests no grant, and refuses root execution. The diagnostic itself is unsandboxed so it can read kernel process metadata. It exposes no external command endpoint.

Three fresh processes pass JavaScript, image, identity, and cleanup checks. JavaScript returns the fresh nonce, an 800 by 600 viewport, and the expected canvas pixel. Each saved PNG measures 1600 by 1200 pixels. Four direct pixel samples match red, green, blue, and white, including opaque alpha.

Two color-accessor changes failed the image check before direct component reads passed. The PNG already contained the expected bytes. The first approach converted colors through AppKit instead of comparing those bytes. Earlier failed calibration results remain in the evidence. This correction changes the measurement, not the renderer.

WebKit creates one invisible TUINSWindow. It never becomes key. The probe creates no explicit NSWindow and observes no visible window. This result does not show that WindowServer access is unnecessary.

Kernel records identify the host and the content, GPU, and network services. Their real, effective, and saved user IDs are all 501. Their group IDs are all 20. Service executable paths and start times remain stable across each snapshot. The private network PID getter can start its service. Its use is explicit in the evidence.

The installed WebKit version is 21624.4.5.11.5. This experiment uses the system framework, not the custom research engine. Session queries succeed and report the console user as 501. Session access alone does not prove correct rendering. The independent JavaScript and image checks supply that evidence.

All measured host and service PIDs disappear after the trials. Two ordinary-user invalid invocations refuse with exit code 64. Frozen browser and probe hashes match milestone 98. No further administrator command ran.

The browser's pause bypass remains open. This baseline supplies no cross-user rendering, protected display, physical input, network compatibility, or general website guarantee. The next ordinary-user step can test a fixed loopback document and image delivery. Any cross-user renderer experiment needs a new reviewed artifact and separate approval.

Run `bash scripts/build-headless-renderer-probe.sh`, then `python3 tools/run_headless_renderer_probe.py --out artifacts/headless-renderer-new`. The output directory must not exist. Keep earlier evidence intact.

See [saved results](evidence/headless-renderer-results.json), [snapshot](evidence/headless-renderer-snapshot.png), and [source research](research/renderer-identity-probe-plan.md).

# Loopback renderer findings

Milestone 100 adds a fixed loopback mode to the separate headless probe. Its controller owns a temporary server on a randomly assigned local port. It leaves the existing fixture servers unchanged. The native app accepts only the exact main document and child-frame paths for its fresh nonce. It refuses other navigation.

Three fresh network trials pass. Each receives the main document, an image, an iframe, and a fetch response. Independent server receipts record all four requests. The owner script reads matching frame and response nonces and a loaded image width. This script is a diagnostic control, not an external agent action.

Six snapshot samples match red, green, blue, white, yellow, and cyan. The latter two come from the network image and child frame. All six pixels have opaque alpha. The image check reads direct components from the encoded PNG. It accepts the expected aspect ratio at the measured scale.

Three inline regression trials also pass after the shared JavaScript helper changes. In all six trials, kernel records identify stable content, GPU, and network services under real, effective, and saved user ID 501. Each app observes one invisible, nonkey framework window and no visible window. Every JavaScript, pixel, identity, and host cleanup check passes.

All measured host and service PIDs disappear after the trials. The temporary server stops and closes its socket. Three invalid port or option invocations refuse with exit code 64. Swift compiles with warnings as errors. Python compilation passes. No administrator command or permission change occurs.

This result covers one disposable local document and its same-origin resources. It does not establish authentication, cross-origin frames, downloads, video, physical input, cross-user rendering, or protection from agents. The browser's known pause bypass remains open. The current same-user services do not supply a new signal boundary.

Run `bash scripts/build-headless-renderer-probe.sh`, then `python3 tools/run_headless_renderer_probe.py --network --out artifacts/headless-loopback-new`. The output directory must not exist. The controller stops at the first inconclusive trial and preserves its evidence.

See [network and regression results](evidence/loopback-renderer-results.json), [network snapshot](evidence/loopback-renderer-snapshot.png), and [earlier baseline](headless-renderer-findings.md).

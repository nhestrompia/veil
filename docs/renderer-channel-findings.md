# Private renderer channel result

Milestone 113 tests whether a paused display process can stop page execution through a full output socket. Three fresh comparisons pass. The nonblocking renderer completes 11, 12, and 11 page samples entirely inside the display pause. Each sample includes JavaScript and an actual WKWebView snapshot. The matched blocking renderer completes zero samples inside each pause. Its snapshots stall across resume for 1192.491, 1195.129, and 1187.748 milliseconds.

All channel apps use ordinary user ID 501. This result covers the transport design only. The browser does not yet connect this channel to the cross-user renderer from milestone 112. Its confirmed same-user renderer-pause bypass remains open. Agent-free operation remains unmet.

## Channel design

The parent creates an anonymous Unix stream socket pair before it starts either child. Each child inherits one descriptor. A 16-byte session value travels through queued socket bytes. The value never enters arguments, logs, or a token file. The channel opens no listener, port, or named service. The disposable fixture server has a separate loopback port.

Each message has a fixed 48-byte header. The decoder checks the magic value, kind, reserved bytes, positive sequence, timestamp, session value, and payload size. Navigation permits at most 2048 bytes. Pixels permit at most two mebibytes. The decoder supports split and concatenated stream messages. A separate check rejects repeated sequences, future timestamps, and expired packets.

The renderer keeps one active frame and one replaceable latest frame. It preserves every byte of a partially sent frame. New frames replace only the pending frame. Nonblocking reads and writes use readiness callbacks with bounded work per callback. The renderer continues page samples after the peer disconnects. No page command can enter through standard input or a public socket.

The diagnostic renderer accepts only its exact disposable fixture address. Navigation expires after 250 milliseconds. The display rejects frames older than 500 milliseconds. These timestamps record message emission, not the original physical device event. Descriptor possession and session checks establish neither human origin nor secure peer enrollment.

## Live comparison

The fixture contains a fresh nonce, a timer, and a noise canvas. Its PNG snapshots measure about 843 kibibytes. The runner reduces the socket send buffer to force real backpressure. It waits for the first decoded image before the calibrated native actor pauses the display for about 1.2 seconds.

The actor checks the exact disposable display executable, process start time, and credentials before each signal. It observes the stopped state. A detached recovery child can resume that same verified display if the actor dies. The actor cannot target the frozen browser.

All three candidates record EAGAIN and replace ten pending frames per trial. Their maximum queued output measures 1,726,052 bytes, below the two-frame bound. After resume, each display rejects an expired frame and assigns fresh decoded images to its NSImageView. After display exit, the page timer advances from 14 to 16, 14 to 16, and 14 to 17.

A separate recovery trial kills the actor after its verified stop. The recovery child resumes the display and exits. All 42 measured process identifiers disappear across the six comparisons and recovery trial. The native apps retain fixed eight-second and eleven-second lifetimes. No visible window, administrator command, privacy grant, or input hook enters these tests.

The first polling-only pilot fails before its first image presentation. It never reaches the pause attack and supplies no protection evidence. Readiness callbacks repair normal frame delivery. A new paired pilot and the final three-pair matrix pass. The saved evidence retains the failed pilot.

## Verification

The standalone channel suite passes 257 checks in both optimized and Address Sanitizer builds. It covers all 72 split points, byte-wise input, malformed headers, replay, expiry, real socket backpressure, final-frame retention, and truncated EOF. A closed peer causes no SIGPIPE. The native metadata regression passes without signals. All 55 existing Python checks pass.

The five frozen permissioned executables retain their hashes. Earlier privileged images and both earlier signal actors remain unchanged. The final matrix records the hashes of the new diagnostic executables. The build script compiles only the new apps, actor profile, and channel suite.

## Integration gates

Cross-user descriptor transfer and peer enrollment remain untested. Both present diagnostics use the same ordinary account. A later launcher must preserve the isolated renderer identity and finite cleanup without granting the ordinary controller privileged commands.

The hidden display proves image decoding and NSImageView assignment. It does not prove physical display usability, capture exclusion, or hardware input. Software sends its initial navigation. The diagnostic is not a protected browser launch path.

The frozen keyboard source recreates NSEvent timestamps at dispatch. It does not propagate original IOHID timestamps. Future input routing must preserve the original device time before expiry can address delayed physical input. No keyboard executable changes in this milestone.

Only the fixed local fixture runs. Arbitrary websites, network and worker progress, physical pointer input, keyboard privacy, and other lifecycle or resource attacks remain open. Passing this transport comparison does not establish a general agent-free browser.

See [saved results](evidence/renderer-channel-results.json), [cross-user progress](renderer-progress-findings.md), and [implementation](implementation.md).

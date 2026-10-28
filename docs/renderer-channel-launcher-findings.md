# Native channel launcher result

Milestone 114 moves private descriptor setup from Python into a finite native launcher. Three ordinary-user controls pass, including inherited ignored and blocked signals. Actual fixture navigation, page samples, and decoded image assignment pass. The renderer continues samples after display exit. Both apps stay hidden.

Deadline, output-limit, stalled-startup, parent-death, process-group termination, and closed-output controls also pass. All 45 measured process identifiers disappear. The final checks find no remaining diagnostic app. This result prepares native launch ownership. It establishes no cross-user or agent-free protection.

## Descriptor ownership

The launcher creates an anonymous Unix socket pair and queues a fresh 16-byte session value in each direction. It clears its temporary session buffer. Neither arguments nor logs contain that value. Each fork-created child receives only its channel endpoint at descriptor three. Standard input uses /dev/null. Standard output and error use a bounded diagnostic pipe.

Each child waits behind its own private gate before execution. The launcher samples both kernel identities, then arms an independent watchdog. The watchdog acknowledges its detached session before either gate opens. The renderer starts first. Its fixed readiness record opens the display gate. The display then sends the fixture navigation through the private channel.

The launcher closes both socket endpoints after the watchdog acknowledgement. The watchdog closes every descriptor except its cancellation and acknowledgement pipes. Neither process retains a duplicate endpoint that could prevent peer EOF. The successful controls observe renderer progress after the display closes its endpoint.

The launcher accepts only the exact disposable loopback fixture format. Its child paths come from the compiled workspace path. It supplies a fixed environment and clears the inherited signal mask. It exposes no arbitrary child path, shell command, public listener, or administrator mode. The executable accepts only this Mac's compiled ordinary user ID 501 and refuses root.

## Finite cleanup

The parent owns and reaps both fork-created app hosts and its watchdog. Cleanup sends signals only to unreaped direct children. The watchdog retains each host's birth time and credentials. After parent death, it rechecks those identities before resuming and terminating either host. It never acts on WebKit identifiers from app output.

The normal deadline is 14 seconds. A stalled-startup control uses three seconds. A separate deadline control uses one second. The parent alarm is 24 seconds, the app-child alarm is 16 seconds, and the detached watchdog alarm is 20 seconds. The watchdog waits at most 17 seconds for cancellation before host cleanup. A blocked report sink receives a half-second relay budget.

The default report limit is 384 kibibytes. The output-limit control uses 1024 bytes. Every interrupted control reports the expected failure rather than success. Killing only the parent and terminating its original process group both leave the detached watchdog able to finish host cleanup. Closing the output reader causes controlled failure and host exit.

Fault checks cover the launcher, both app hosts, and watchdog. Auxiliary WebKit process coverage is incomplete after interrupted runs because their final reports can disappear. Normal completed runs also check reported WebKit roles. The result does not prove cleanup of every possible auxiliary process.

## Verification and evidence

The final matrix passes three normal trials, three controlled-failure trials, three parent/output faults, and six invocation refusals. Clang static analysis reports zero diagnostics. The new launcher has hardened runtime and loads only libSystem. All code runs as the ordinary user. No administrator command, privacy change, input hook, or visible window runs.

The first pilot reaches a successful native result, then its Python collector fails on a set operation. That pilot remains inconclusive in the evidence. The repaired collector records independent cleanup before the final matrix.

Five frozen permissioned executables, earlier privileged images, and all milestone 113 diagnostic images retain their hashes. No existing renderer, permissioned app, or root supervisor is rebuilt. See [saved results](evidence/renderer-channel-launcher-results.json) and [channel comparison](renderer-channel-findings.md).

## Remaining integration gate

The launcher and its app paths remain ordinary-user owned. An agent with that account can alter them or launch its own diagnostics. Private descriptors do not establish human origin or secure peer enrollment. Every current launcher process remains vulnerable to same-user suspension.

Cross-user integration therefore needs a separate reviewed launcher or isolated coordinator. That work must preserve descriptor ownership, bounded output, host cleanup, and the permanent credential drop. Earlier administrator approvals are consumed. This milestone contains no new privileged proposal or authorization request.

The normal browser still has its confirmed renderer-pause bypass. Physical input, original hardware timestamps, capture exclusion, privacy gaps, and arbitrary website compatibility remain open. Agent-free operation remains unmet.

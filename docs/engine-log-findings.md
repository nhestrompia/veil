# Quiet-log correction

The zero-exit/no-output messages did not prove Swift compilation failure. A forced PAL Swift compile reproduced that message in quiet mode. It exited zero and regenerated its object file. The same target also passed with warnings enabled in normal logging.

The earlier full builds stopped through manual monitor interrupts before their final exit status. Their cache-failure attribution was unsupported. Those records establish interrupted experiments, not failed complete builds. The missing configurations, Metal compiler, and sandboxed temporary-directory failures remain separate, confirmed failures.

The build now uses normal logging and upstream cache defaults. Its log limit is 512 MiB. The disk reserve, four jobs, reduced priority, and two-hour limit remain. Future receipts explicitly distinguish running, succeeded, failed, and stopped states. Exceptions include their class name, so an interrupt cannot leave an empty reason.

The seventh full build is active. It reached WebCore compilation. A complete build requires the recorded command exit code. Runtime acceptance also requires expected loaded images and live comparisons. Log severity words alone do not establish a build outcome.

All 102 Python checks pass. Two checks execute real child processes to test success despite error wording and failure on a nonzero exit. The real PAL reproduction remains separate from those small harness checks.

See [saved evidence](evidence/engine-log-results.json).

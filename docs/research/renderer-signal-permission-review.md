# Renderer signal permission review

Checked October 26, 2026. This review separates signal permission from page behavior. It authorizes no privileged execution.

Apple XNU checks mandatory access-control policy before its ordinary signal permission function. That function permits SIGCONT between processes in the same POSIX session. It then compares the sender's real or effective user identity with the target's real or saved identity. Root has a separate allowance. [Apple signal implementation](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/kern_sig.c).

Thus a cross-user SIGCONT success can be consistent with the documented source. It does not show that the sender can stop a running target. Record the actual signal results and both POSIX session identifiers. Do not confuse POSIX sessions with the Security framework session record. The installed kernel can differ from the reviewed source, so runtime evidence remains required.

The actor must bind every target to the fresh fixed probe report. Kernel paths, credentials, and start times strengthen that binding but do not independently establish WebKit role ownership. The root supervisor must never use reported service identifiers as privileged signal targets. Its owned-child watchdog is a separate recovery mechanism.

The observer cannot open the root-owned supervisor image at mode 0700. Root staging verifies that image's hash. The ordinary observer checks its metadata and hashes the readable app files. Relaxing helper permissions to simplify observation would expand access without a test need.

Independent review caught and corrected premature observation-file permission changes and an attempt to reopen a readonly file. The final shell opens its write descriptor exclusively while staging is private. It then seals the file and publishes the directory. The ordinary observer waits through the private phase.

Reference controls show actual stopped states and successful recovery. Their state samples exclude zombies. These controls do not establish post-attack website progress. The fixture report precedes the signal attempts. Neither a renderer smoke test nor a permission test establishes a feature-complete agent-free browser.

The reviewed proposal needs a fresh one-run administrator approval. Keep shared-account, cache, inherited-session, auxiliary-lifecycle, and staging-residue limits explicit. See [the proposal and controls](../renderer-signal-preflight-findings.md).

# Identity and signal experiment plan

Checked 2026-10-26. Status: proposed command-line experiment. No privileged test ran for this note.

A different user ID could stop the measured same-user SIGSTOP attack. This is a hypothesis about one operating-system boundary. It does not prove an agent-free browser. The existing browser still has the measured [pause bypass](../clock-channel-findings.md).

## Permission rule

Apple's current published XNU source compares the sender's real or effective user ID with the target's real or saved user ID. Root bypasses that comparison. The same-session SIGCONT exception also matters. The source applies a mandatory-access-control check before this comparison. Apple's archived manual gives a broader description, so use the live experiment to test this Mac. [XNU signal checks](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/kern_sig.c), [Apple kill manual](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/kill.2.html).

A successful cross-user control would support a narrow inference: the tested ordinary user cannot send SIGSTOP to that isolated child. It would say nothing about root attackers, other suspension APIs, or browser integration.

## Permanent identity change

The proposed parent forks disposable targets and senders. Each child replaces its supplementary groups, then calls `setgid`, then `setuid`. Every failed call stops that trial. Apple requires group changes before the user change. `setgroups` needs root. Privileged `setgid` and `setuid` change the real, effective, and saved IDs. An effective-ID change alone leaves a recoverable identity and invalidates this control. [Apple privilege guide](https://developer.apple.com/library/archive/documentation/Security/Conceptual/SecureCodingGuide/Articles/AccessControl.html), [Apple group list manual](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/setgroups.2.html), [Apple identity manual](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/setuid.2.html), [XNU identity implementation](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/kern_prot.c).

Use the existing `nobody` account on this Mac. The parent reports UID and GID `4294967294`, Darwin's unsigned representation of minus two. Do not assume `65534` or the account name `_nobody`. Compile the invoking user's UID and GID into the reviewed test. Reject zero IDs and identical sender and isolated-target IDs. This experiment creates no account.

The parent reads `PROC_PIDTBSDINFO` after each change. Require `pbi_uid`, `pbi_ruid`, and `pbi_svuid` to match the intended UID. Require the equivalent three GID fields to match. XNU fills these fields from the process credentials. Also check the supplementary group list and failed attempts to regain root. [XNU process fields](https://raw.githubusercontent.com/apple-oss-distributions/xnu/main/bsd/sys/proc_info.h), [XNU process information](https://raw.githubusercontent.com/apple-oss-distributions/xnu/main/bsd/kern/proc_info.c).

## Finite test and evidence

The following is a proposed procedure. Root execution requires a separate, reviewed action. This note does not authorize or perform it.

1. Stage the reviewed native binary in a private temporary directory owned by root. Compare its hash after the copy.
2. Start the parent with a cleared environment and a fixed deadline. Accept no runtime PID, executable path, or UID.
3. Fork a same-user target, an isolated target, and senders with the compiled invoking identity. Check credentials before signal attempts.
4. Test only those children with SIGSTOP. Record return values, `errno`, target heartbeats, and the parent's independent stop status.
5. Resume and reap each owned child. Remove only the exact temporary files from this run.

The same-user control must return success and reach `WIFSTOPPED` with `WSTOPSIG` equal to SIGSTOP. The parent then resumes it. The cross-user trial must return `EPERM`, show no stop, and retain heartbeat progress. A missing heartbeat alone proves neither blocking nor suspension. `waitpid` supplies child status with `WNOHANG` and `WUNTRACED`. [Apple wait manual](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/wait4.2.html).

The parent must retain each unreaped child's identity, parent PID, and start time. Cleanup signals use positive, owned child PIDs only. A timeout or ordinary interruption triggers cleanup. Parent death under SIGKILL remains a separate recovery question.

## Executable trust and limits

Here, immutable means the attacker cannot replace the staged binary or its dependencies. It does not mean a filesystem immutable flag. Root ownership alone is insufficient when a writable parent directory permits replacement. Check directory ownership, modes, access-control lists, and symlinks. Check the native binary and dynamic-library paths before privileged launch. Checks inside `main` occur after the loader runs. Apple's privileged-helper guidance also requires control of inherited descriptors and environment variables. [Apple privileged-helper guidance](https://developer.apple.com/library/archive/documentation/Security/Conceptual/SecureCodingGuide/Articles/AccessControl.html).

No set-user-ID bit, service, entitlement, permission grant, or persistent account belongs in this experiment. The parent stays root only for its finite child lifecycle. Its child protocol accepts no arbitrary command.

A positive result would justify a separate isolated-renderer prototype. The shared `nobody` identity is unsuitable as the browser's final private identity. Other processes with that identity retain matching signal credentials. A future browser also needs trusted launch, narrowly scoped interprocess messages, and protected storage. User-side UI, WindowServer access, rendering, physical input, and recovery remain open. An unprotected UI or network process could preserve the pause attack. This command-line result cannot establish prevention across websites or operating-system agents.

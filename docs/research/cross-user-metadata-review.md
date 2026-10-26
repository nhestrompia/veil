# Cross-user metadata review

Checked October 26, 2026. This review concerns a finite diagnostic reader, not browser runtime policy. It authorizes no privileged execution.

Apple XNU's proc-info dispatch applies its default same-effective-user check to PROC_PIDTBSDINFO. It exempts PROC_PIDPATHINFO from that credential comparison. Mandatory access-control checks still precede these queries. The wrapper returns zero when the underlying call fails. [Apple dispatch policy](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/proc_info.c#L2074), [credential comparison](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/proc_info.c#L2980), [libproc wrapper](https://github.com/apple-oss-distributions/xnu/blob/main/libsyscall/wrappers/libproc/libproc.c).

KERN_PROC_PID uses a separate readonly sysctl handler. It selects the requested process and exports start time, state, and process credentials. Apple labels these process nodes SPI for system tools and libraries. Their availability is a measured diagnostic property, not a supported security guarantee across future releases. [Apple handler and compatibility warning](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/kern_sysctl.c#L794), [credential export](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/kern_sysctl.c#L1014).

The exported effective group is the first group entry. Validate the group count before indexing. The real and saved user/group fields come from the exported process credentials. Use the installed SDK structure, never a hardcoded byte count. [Apple group definition](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/sys/ucred.h#L202).

The local capability test returns 136 bytes for same-user BSD info and 648 bytes for the sysctl structure. Both values describe this build. Init's BSD query returns EPERM, while its path and sysctl query succeed. The actual actor-reader regression reproduces the foreign-user failure before the change and passes afterward.

The repaired reader samples sysctl identity before and after the path query. It requires matching PID, all six credentials, and start time. It retains another immediate check before signals. These separate calls cannot supply an atomic process handle. A target can exit or execute another image between checks.

Stopped and zombie states cannot serve as valid initial targets. A different sampled state does not establish website progress. PID 1 readability also does not prove that every WebKit role is readable. Any missing data or mismatch must refuse before signal attempts. [Apple state definitions](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/sys/proc.h#L153).

Independent static review found no concrete blocker in this ordinary-user change. It retained the earlier same-session SIGCONT distinction and the root supervisor's owned-child-only cleanup. Any further administrator launch still needs the fresh bounded approval described in [the findings](../renderer-metadata-findings.md).

#include <errno.h>
#include <inttypes.h>
#include <libproc.h>
#include <signal.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <sys/proc.h>
#include <sys/sysctl.h>
#include <sys/wait.h>
#include <unistd.h>

static bool inspect(const char *name, pid_t pid)
{
    struct proc_bsdinfo bsd = {0};
    errno = 0;
    int bsd_size = proc_pidinfo(pid, PROC_PIDTBSDINFO, 0, &bsd, sizeof(bsd));
    int bsd_error = errno;
    char path[PROC_PIDPATHINFO_MAXSIZE];
    errno = 0;
    int path_size = proc_pidpath(pid, path, sizeof(path));
    int path_error = errno;
    struct kinfo_proc kernel = {0};
    size_t size = sizeof(kernel);
    int mib[] = {CTL_KERN, KERN_PROC, KERN_PROC_PID, pid};
    errno = 0;
    int result = sysctl(mib, 4, &kernel, &size, NULL, 0), sysctl_error = errno;
    bool bsd_valid = bsd_size == sizeof(bsd);
    bool kernel_valid = result == 0 && size == sizeof(kernel) && kernel.kp_proc.p_pid == pid;
    bool parity = bsd_valid && kernel_valid && bsd.pbi_uid == kernel.kp_eproc.e_ucred.cr_uid
        && bsd.pbi_ruid == kernel.kp_eproc.e_pcred.p_ruid && bsd.pbi_svuid == kernel.kp_eproc.e_pcred.p_svuid
        && bsd.pbi_gid == kernel.kp_eproc.e_ucred.cr_groups[0]
        && bsd.pbi_rgid == kernel.kp_eproc.e_pcred.p_rgid && bsd.pbi_svgid == kernel.kp_eproc.e_pcred.p_svgid
        && bsd.pbi_start_tvsec == (uint64_t)kernel.kp_proc.p_starttime.tv_sec
        && bsd.pbi_start_tvusec == (uint64_t)kernel.kp_proc.p_starttime.tv_usec
        && bsd.pbi_status == (uint32_t)kernel.kp_proc.p_stat;
    printf("%s\"%s\":{\"pid\":%d,\"bsdBytes\":%d,\"bsdExpectedBytes\":%zu,\"bsdErrno\":%d,\"pathBytes\":%d,\"pathErrno\":%d,\"sysctlReturn\":%d,\"sysctlErrno\":%d,\"sysctlBytes\":%zu,\"sysctlExpectedBytes\":%zu,\"sysctlValid\":%s,\"metadataParity\":%s",
        !strcmp(name, "self") ? "" : ",", name, pid, bsd_size, sizeof(bsd), bsd_error, path_size, path_error,
        result, sysctl_error, size, sizeof(kernel), kernel_valid ? "true" : "false", parity ? "true" : "false");
    if (kernel_valid)
        printf(",\"kernel\":{\"realUID\":%u,\"effectiveUID\":%u,\"savedUID\":%u,\"realGID\":%u,\"effectiveGID\":%u,\"savedGID\":%u,\"startedSeconds\":%" PRId64 ",\"startedMicroseconds\":%d,\"status\":%d}",
            kernel.kp_eproc.e_pcred.p_ruid, kernel.kp_eproc.e_ucred.cr_uid, kernel.kp_eproc.e_pcred.p_svuid,
            kernel.kp_eproc.e_pcred.p_rgid, kernel.kp_eproc.e_ucred.cr_groups[0], kernel.kp_eproc.e_pcred.p_svgid,
            (int64_t)kernel.kp_proc.p_starttime.tv_sec, kernel.kp_proc.p_starttime.tv_usec, kernel.kp_proc.p_stat);
    printf("}");
    return parity;
}

int main(int argc, char **argv)
{
    (void)argv;
    if (argc != 1 || getuid() == 0 || geteuid() == 0) return 64;
    alarm(8);
    int gate[2];
    if (pipe(gate)) return 65;
    pid_t child = fork();
    if (child < 0) return 65;
    if (!child) {
        alarm(5);
        close(gate[1]);
        char byte;
        read(gate[0], &byte, 1);
        _exit(0);
    }
    close(gate[0]);
    printf("{\"actorUID\":%u,\"signalCalls\":0,\"rootRun\":false,\"samples\":{", getuid());
    bool self = inspect("self", getpid());
    bool owned = inspect("ownedChild", child);
    inspect("systemInitReadOnly", 1);
    close(gate[1]);
    int status = 0;
    pid_t waited;
    do { waited = waitpid(child, &status, 0); } while (waited < 0 && errno == EINTR);
    bool reaped = waited == child && WIFEXITED(status) && WEXITSTATUS(status) == 0;
    printf("},\"ownedChildReaped\":%s,\"ownMetadataParity\":%s}\n", reaped ? "true" : "false", self && owned ? "true" : "false");
    return self && owned && reaped ? 0 : 1;
}

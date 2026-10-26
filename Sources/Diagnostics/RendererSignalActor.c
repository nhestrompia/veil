#include <ctype.h>
#include <errno.h>
#include <libproc.h>
#include <limits.h>
#include <poll.h>
#include <pwd.h>
#include <signal.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/proc.h>
#include <sys/stat.h>
#include <sys/sysctl.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#ifndef AFB_RESEARCH_UID
#error Compile with the ordinary research user ID.
#endif

#ifdef AFB_PROGRESS_CONTROL
#define AFB_RENDERER_NAME "RendererProgressProbe"
#else
#define AFB_RENDERER_NAME "RendererIdentityProbe"
#endif

struct target {
    pid_t pid;
    struct proc_bsdinfo identity;
    char path[PROC_PIDPATHINFO_MAXSIZE];
};

static double monotonic(void)
{
    struct timespec value;
    if (clock_gettime(CLOCK_MONOTONIC, &value)) _exit(70);
    return value.tv_sec + value.tv_nsec / 1e9;
}

static void delay(unsigned milliseconds)
{
    struct timespec value = {milliseconds / 1000, (milliseconds % 1000) * 1000000};
    while (nanosleep(&value, &value) && errno == EINTR) { }
}

static bool number(const char *text, uint64_t *value)
{
    if (!*text || strspn(text, "0123456789") != strlen(text)) return false;
    errno = 0;
    char *end;
    *value = strtoull(text, &end, 10);
    return !errno && !*end;
}

struct metadata_failure {
    const char *api;
    int error;
    size_t bytes;
};

static bool same_metadata(const struct proc_bsdinfo *first, const struct proc_bsdinfo *second)
{
    return first->pbi_pid == second->pbi_pid && first->pbi_start_tvsec == second->pbi_start_tvsec
        && first->pbi_start_tvusec == second->pbi_start_tvusec && first->pbi_uid == second->pbi_uid
        && first->pbi_ruid == second->pbi_ruid && first->pbi_svuid == second->pbi_svuid
        && first->pbi_gid == second->pbi_gid && first->pbi_rgid == second->pbi_rgid && first->pbi_svgid == second->pbi_svgid;
}

static bool read_kernel_identity(pid_t pid, struct proc_bsdinfo *identity, struct metadata_failure *failure, const char *api)
{
    *failure = (struct metadata_failure){api, EINVAL, 0};
    if (pid <= 0) return false;
    memset(identity, 0, sizeof(*identity));
    struct kinfo_proc info = {0};
    size_t size = sizeof(info);
    int mib[] = {CTL_KERN, KERN_PROC, KERN_PROC_PID, pid};
    errno = 0;
    int result = sysctl(mib, 4, &info, &size, NULL, 0);
    failure->error = result ? errno : ESRCH;
    failure->bytes = size;
    if (result || size != sizeof(info) || info.kp_proc.p_pid != pid) return false;
    if (info.kp_eproc.e_ucred.cr_ngroups < 1 || info.kp_eproc.e_ucred.cr_ngroups > NGROUPS
        || info.kp_proc.p_starttime.tv_sec <= 0 || info.kp_proc.p_starttime.tv_usec < 0
        || info.kp_proc.p_starttime.tv_usec >= 1000000) {
        failure->error = EPROTO;
        return false;
    }
    identity->pbi_pid = pid;
    identity->pbi_uid = info.kp_eproc.e_ucred.cr_uid;
    identity->pbi_ruid = info.kp_eproc.e_pcred.p_ruid;
    identity->pbi_svuid = info.kp_eproc.e_pcred.p_svuid;
    identity->pbi_gid = info.kp_eproc.e_ucred.cr_groups[0];
    identity->pbi_rgid = info.kp_eproc.e_pcred.p_rgid;
    identity->pbi_svgid = info.kp_eproc.e_pcred.p_svgid;
    identity->pbi_start_tvsec = info.kp_proc.p_starttime.tv_sec;
    identity->pbi_start_tvusec = info.kp_proc.p_starttime.tv_usec;
    identity->pbi_status = info.kp_proc.p_stat;
    return true;
}

static bool read_target_detailed(pid_t pid, struct target *value, struct metadata_failure *failure)
{
    struct metadata_failure ignored;
    if (!failure) failure = &ignored;
    memset(value, 0, sizeof(*value));
    if (!read_kernel_identity(pid, &value->identity, failure, "sysctl-kern-proc-pid")) return false;
    value->pid = pid;
    failure->api = "proc-pidpath";
    errno = 0;
    int length = proc_pidpath(pid, value->path, sizeof(value->path));
    failure->error = errno;
    failure->bytes = length > 0 ? (size_t)length : 0;
    if (length <= 0) return false;
    struct proc_bsdinfo after;
    if (!read_kernel_identity(pid, &after, failure, "sysctl-kern-proc-pid-recheck")) return false;
    if (!same_metadata(&value->identity, &after)) {
        failure->error = EAGAIN;
        return false;
    }
    value->identity.pbi_status = after.pbi_status;
    return true;
}

static bool read_target(pid_t pid, struct target *value)
{
    return read_target_detailed(pid, value, NULL);
}

static bool unchanged(const struct target *expected, struct target *current)
{
    return read_target(expected->pid, current) && !strcmp(expected->path, current->path)
        && same_metadata(&expected->identity, &current->identity);
}

static bool host_path(const char *path, bool isolated)
{
    if (!isolated) {
        char root[PATH_MAX];
        if (snprintf(root, sizeof(root), "%s", __FILE__) >= (int)sizeof(root)) return false;
        for (unsigned i = 0; i < 3; ++i) {
            char *end = strrchr(root, '/');
            if (!end) return false;
            *end = 0;
        }
        char expected[PATH_MAX];
        int count = snprintf(expected, sizeof(expected), "%s/dist/" AFB_RENDERER_NAME ".app/Contents/MacOS/" AFB_RENDERER_NAME, root);
        return count > 0 && count < (int)sizeof(expected) && !strcmp(expected, path);
    }
    const char *prefix = "/private/tmp/agentfreebrowser-renderer.";
    size_t length = strlen(prefix);
    if (strncmp(path, prefix, length) || strlen(path) <= length + 6) return false;
    for (size_t i = 0; i < 6; ++i)
        if (!isalnum((unsigned char)path[length + i])) return false;
    if (strcmp(path + length + 6, "/" AFB_RENDERER_NAME ".app/Contents/MacOS/" AFB_RENDERER_NAME)) return false;
    char directory[PATH_MAX];
    memcpy(directory, path, length + 6);
    directory[length + 6] = 0;
    struct stat stage, binary;
    return !lstat(directory, &stage) && S_ISDIR(stage.st_mode) && stage.st_uid == 0
        && (stage.st_mode & 07777) == 0711 && !lstat(path, &binary) && S_ISREG(binary.st_mode)
        && binary.st_uid == 0 && binary.st_nlink == 1 && (binary.st_mode & 07777) == 0555;
}

static bool service_path(const char *path, unsigned role)
{
    const char *names[] = {"", "WebContent", "GPU", "Networking"};
    const char *prefixes[] = {"", "/System/Volumes/Preboot/Cryptexes/OS"};
    for (unsigned i = 0; i < 2; ++i) {
        char expected[PATH_MAX];
        int count = snprintf(expected, sizeof(expected), "%s/System/Library/Frameworks/WebKit.framework/Versions/A/XPCServices/com.apple.WebKit.%s.xpc/Contents/MacOS/com.apple.WebKit.%s", prefixes[i], names[role], names[role]);
        if (count > 0 && count < (int)sizeof(expected) && !strcmp(path, expected)) return true;
    }
    return false;
}

static void recovery(const struct target targets[4], int cancellation, int ready)
{
    alarm(6);
    int maximum = getdtablesize();
    for (int fd = 0; fd < maximum; ++fd)
        if (fd != cancellation && fd != ready) close(fd);
    if (setsid() != getpid()) _exit(71);
    if (write(ready, "r", 1) != 1) _exit(71);
    close(ready);
    struct pollfd item = {cancellation, POLLIN, 0};
    int found = poll(&item, 1, 4000);
    char byte = 0;
    if (found > 0 && read(cancellation, &byte, 1) == 1 && byte == 'q') _exit(0);
    for (unsigned i = 0; i < 4; ++i) {
        struct target current;
        if (unchanged(&targets[i], &current)) kill(targets[i].pid, SIGCONT);
    }
    _exit(0);
}

int main(int argc, char **argv)
{
    if (getuid() != AFB_RESEARCH_UID || geteuid() != AFB_RESEARCH_UID || argc != 14) return 64;
    bool isolated = !strcmp(argv[1], "--cross-user");
    if (!isolated && strcmp(argv[1], "--reference")) return 64;
    sigset_t mask;
    sigemptyset(&mask);
    if (sigprocmask(SIG_SETMASK, &mask, NULL)) return 65;
    int defaults[] = {SIGALRM, SIGCHLD, SIGTERM, SIGINT, SIGHUP, SIGQUIT, SIGPIPE};
    for (unsigned i = 0; i < sizeof(defaults)/sizeof(defaults[0]); ++i)
        if (signal(defaults[i], SIG_DFL) == SIG_ERR) return 65;
    alarm(8);
    setvbuf(stdout, NULL, _IONBF, 0);
    struct passwd *account = getpwnam("nobody");
    if (!account || !account->pw_uid || account->pw_uid == getuid() || !account->pw_gid) return 65;
    uid_t uid = isolated ? account->pw_uid : getuid();
    gid_t gid = isolated ? account->pw_gid : getgid();
    struct target targets[4];
    for (unsigned i = 0; i < 4; ++i) {
        uint64_t pid, seconds, microseconds;
        if (!number(argv[2 + i*3], &pid) || pid <= 1 || pid > INT_MAX
            || !number(argv[3 + i*3], &seconds) || !number(argv[4 + i*3], &microseconds) || microseconds >= 1000000)
            return 64;
        struct metadata_failure failure;
        if (!read_target_detailed((pid_t)pid, &targets[i], &failure)) {
            const char *role_names[] = {"host", "content", "gpu", "network"};
            printf("SIGNAL_SCOPE_REFUSAL {\"role\":\"%s\",\"pid\":%d,\"api\":\"%s\",\"errno\":%d,\"bytes\":%zu,\"signalCallsSent\":0}\n",
                role_names[i], (pid_t)pid, failure.api, failure.error, failure.bytes);
            return 65;
        }
        struct proc_bsdinfo *info = &targets[i].identity;
        if ((i == 0 ? !host_path(targets[i].path, isolated) : !service_path(targets[i].path, i))) return 66;
        if (info->pbi_start_tvsec != seconds || info->pbi_start_tvusec != microseconds
            || info->pbi_uid != uid || info->pbi_ruid != uid || info->pbi_svuid != uid
            || info->pbi_gid != gid || info->pbi_rgid != gid || info->pbi_svgid != gid
            || info->pbi_status == SSTOP || info->pbi_status == SZOMB)
            return 67;
        for (unsigned j = 0; j < i; ++j) if (targets[j].pid == (pid_t)pid) return 68;
    }
    int cancellation[2], ready[2];
    if (pipe(cancellation) || pipe(ready)) return 69;
    pid_t guard = fork();
    if (guard < 0) return 69;
    if (!guard) recovery(targets, cancellation[0], ready[1]);
    close(cancellation[0]); close(ready[1]);
    struct pollfd armed = {ready[0], POLLIN, 0};
    char byte = 0;
    if (poll(&armed, 1, 1000) <= 0 || read(ready[0], &byte, 1) != 1 || byte != 'r'
        || getsid(guard) != guard || getpgid(guard) != guard) return 69;
    close(ready[0]);
    bool passed = true, recovered = true;
    const char *names[] = {"host", "content", "gpu", "network"};
    for (unsigned i = 0; i < 4; ++i) {
        struct target current;
        if (!unchanged(&targets[0], &current) || !unchanged(&targets[i], &current)
            || current.identity.pbi_status == SSTOP || current.identity.pbi_status == SZOMB) {
            passed = false;
            break;
        }
        errno = 0;
        int stopped = kill(targets[i].pid, SIGSTOP), stop_error = errno;
        bool observed = false;
        if (!stopped) {
            double deadline = monotonic() + 0.1;
            do {
                if (!unchanged(&targets[i], &current)) break;
                observed = current.identity.pbi_status == SSTOP;
                if (observed) break;
                delay(1);
            } while (monotonic() < deadline);
            printf("SIGNAL_STOPPED {\"role\":\"%s\",\"pid\":%d,\"watchdogPID\":%d,\"observed\":%s}\n", names[i], targets[i].pid, guard, observed ? "true" : "false");
            delay(100);
        }
        bool stable = unchanged(&targets[i], &current);
        errno = 0;
        int continued = stable ? kill(targets[i].pid, SIGCONT) : -1;
        int continue_error = stable ? errno : ESRCH;
        double deadline = monotonic() + 0.1;
        bool not_stopped = false;
        do {
            stable = unchanged(&targets[i], &current);
            not_stopped = stable && current.identity.pbi_status != SSTOP && current.identity.pbi_status != SZOMB;
            if (not_stopped || !stable) break;
            delay(1);
        } while (monotonic() < deadline);
        if (!stopped && (!continued && not_stopped) == false) recovered = false;
        pid_t actor_session = getsid(0), target_session = getsid(targets[i].pid);
        bool session_continue = continued == 0 && actor_session > 0 && actor_session == target_session;
        bool continue_expected = (continued == -1 && continue_error == EPERM) || session_continue;
        bool expected = isolated ? stopped == -1 && stop_error == EPERM && continue_expected && not_stopped
            : stopped == 0 && observed && continued == 0 && not_stopped;
        passed = passed && expected && stable;
        printf("SIGNAL_RESULT {\"metadataAPI\":\"sysctl-kern-proc-pid-and-proc-pidpath\",\"role\":\"%s\",\"pid\":%d,\"actorUID\":%u,\"targetUID\":%u,\"stopReturn\":%d,\"stopErrno\":%d,\"observedStopped\":%s,\"continueReturn\":%d,\"continueErrno\":%d,\"actorPOSIXSession\":%d,\"targetPOSIXSession\":%d,\"sameSessionContinue\":%s,\"identityStable\":%s,\"notStoppedAfter\":%s,\"expectedOutcome\":%s}\n",
            names[i], targets[i].pid, getuid(), uid, stopped, stop_error, observed ? "true" : "false", continued, continue_error,
            actor_session, target_session, session_continue ? "true" : "false", stable ? "true" : "false", not_stopped ? "true" : "false", expected ? "true" : "false");
        if (!recovered) break;
    }
    if (recovered) {
        signal(SIGPIPE, SIG_IGN);
        if (write(cancellation[1], "q", 1) != 1) passed = false;
    }
    close(cancellation[1]);
    int status = 0;
    pid_t found;
    do { found = waitpid(guard, &status, 0); } while (found < 0 && errno == EINTR);
    bool reaped = found == guard && WIFEXITED(status) && WEXITSTATUS(status) == 0;
    printf("SIGNAL_ACTOR_RESULT {\"crossUser\":%s,\"recoveryComplete\":%s,\"watchdogReaped\":%s,\"passed\":%s}\n",
        isolated ? "true" : "false", recovered ? "true" : "false", reaped ? "true" : "false", passed && reaped ? "true" : "false");
    return passed && reaped ? 0 : 1;
}

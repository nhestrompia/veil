#include <errno.h>
#include <fcntl.h>
#include <libproc.h>
#include <limits.h>
#include <mach-o/dyld.h>
#include <poll.h>
#include <pwd.h>
#include <signal.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/resource.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#ifndef AFB_RESEARCH_UID
#error Compile with the ordinary research user ID.
#endif

struct child { pid_t pid; bool reaped; int status; struct proc_bsdinfo identity; };

static double now(void)
{
    struct timespec value;
    if (clock_gettime(CLOCK_MONOTONIC, &value)) _exit(70);
    return value.tv_sec + value.tv_nsec / 1e9;
}

static void delay(void)
{
    struct timespec value = {0, 10000000};
    while (nanosleep(&value, &value) && errno == EINTR) { }
}

static bool same_child(const struct child *child)
{
    struct proc_bsdinfo info;
    return child->pid > 1 && proc_pidinfo(child->pid, PROC_PIDTBSDINFO, 0, &info, sizeof(info)) == sizeof(info)
        && info.pbi_start_tvsec == child->identity.pbi_start_tvsec
        && info.pbi_start_tvusec == child->identity.pbi_start_tvusec
        && info.pbi_uid == child->identity.pbi_uid && info.pbi_ruid == child->identity.pbi_ruid
        && info.pbi_svuid == child->identity.pbi_svuid && info.pbi_gid == child->identity.pbi_gid
        && info.pbi_rgid == child->identity.pbi_rgid && info.pbi_svgid == child->identity.pbi_svgid;
}

static bool reap(struct child *child, bool terminate)
{
    if (child->pid <= 1 || child->reaped) return true;
    pid_t result = waitpid(child->pid, &child->status, WNOHANG);
    if (result == child->pid) { child->reaped = true; return true; }
    if (result < 0) return false;
    if (!terminate) return true;
    // An unreaped direct child cannot lose its PID to another process.
    kill(child->pid, SIGCONT);
    kill(child->pid, SIGTERM);
    double deadline = now() + 1;
    do {
        result = waitpid(child->pid, &child->status, WNOHANG);
        if (result == child->pid) { child->reaped = true; return true; }
        if (result < 0 && errno != EINTR) return false;
        delay();
    } while (now() < deadline);
    kill(child->pid, SIGKILL);
    do { result = waitpid(child->pid, &child->status, 0); } while (result < 0 && errno == EINTR);
    child->reaped = result == child->pid;
    return child->reaped;
}

static int duplicate(int fd)
{
    int result = fcntl(fd, F_DUPFD_CLOEXEC, 64);
    if (result < 0) _exit(71);
    return result;
}

static void close_from(int first)
{
    int maximum = getdtablesize();
    for (int fd = first; fd < maximum; ++fd) close(fd);
}

#ifdef AFB_PRIVILEGED_CHANNEL_CONTROL
static bool permanent_drop(uid_t uid, gid_t gid)
{
    if (!uid || !gid || setgroups(1, &gid) || setgid(gid) || setuid(uid)) return false;
    struct proc_bsdinfo info;
    gid_t groups[64];
    if (proc_pidinfo(getpid(), PROC_PIDTBSDINFO, 0, &info, sizeof(info)) != sizeof(info)
        || info.pbi_uid != uid || info.pbi_ruid != uid || info.pbi_svuid != uid
        || info.pbi_gid != gid || info.pbi_rgid != gid || info.pbi_svgid != gid
        || getgroups(64, groups) != 1 || groups[0] != gid) return false;
    errno = 0;
    if (setuid(0) != -1 || errno != EPERM) return false;
    errno = 0;
    return setgid(0) == -1 && errno == EPERM;
}

static bool protected_path(const char *path, mode_t mode, bool directory)
{
    struct stat info;
    return !lstat(path, &info) && info.st_uid == 0 && (info.st_mode & 07777) == mode
        && (directory ? S_ISDIR(info.st_mode) : S_ISREG(info.st_mode) && info.st_nlink == 1);
}

static bool staged_paths(char paths[2][PATH_MAX], const char *names[2])
{
    char executable[PATH_MAX], stage[PATH_MAX];
    uint32_t size = sizeof(executable);
    if (_NSGetExecutablePath(executable, &size) || !realpath(executable, stage)
        || !protected_path(stage, 0700, false)) return false;
    char *name = strrchr(stage, '/');
    if (!name || strcmp(name, "/renderer-channel-supervisor")) return false;
    *name = 0;
    const char *prefix = "/private/tmp/agentfreebrowser-renderer.";
    size_t length = strlen(prefix);
    if (strncmp(stage, prefix, length) || strlen(stage) != length + 6
        || strspn(stage + length, "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz") != 6
        || !protected_path(stage, 0711, true)) return false;
    for (unsigned i = 0; i < 2; ++i) {
        const char *directories[] = {"", "/Contents", "/Contents/MacOS", "/Contents/_CodeSignature"};
        const char *files[] = {"Contents/Info.plist", "Contents/_CodeSignature/CodeResources"};
        for (unsigned j = 0; j < 4; ++j) {
            char path[PATH_MAX];
            if (snprintf(path, sizeof(path), "%s/%s.app%s", stage, names[i], directories[j]) >= (int)sizeof(path)
                || !protected_path(path, 0555, true)) return false;
        }
        for (unsigned j = 0; j < 2; ++j) {
            char path[PATH_MAX];
            if (snprintf(path, sizeof(path), "%s/%s.app/%s", stage, names[i], files[j]) >= (int)sizeof(path)
                || !protected_path(path, 0444, false)) return false;
        }
        if (snprintf(paths[i], PATH_MAX, "%s/%s.app/Contents/MacOS/%s", stage, names[i], names[i]) >= PATH_MAX
            || !protected_path(paths[i], 0555, false)) return false;
    }
    return true;
}
#endif

static void execute(const char *application, const char *url, int socket, int output, int gate,
                    int readiness, bool privileged, uid_t uid, gid_t gid)
{
    alarm(16);
    int channel_copy = duplicate(socket), output_copy = duplicate(output), gate_copy = duplicate(gate), ready_copy = duplicate(readiness);
    int null = open("/dev/null", O_RDONLY | O_NOFOLLOW);
    if (null < 0 || dup2(null, 0) < 0 || dup2(output_copy, 1) < 0 || dup2(output_copy, 2) < 0
        || dup2(channel_copy, 3) < 0 || dup2(gate_copy, 4) < 0 || dup2(ready_copy, 5) < 0) _exit(71);
    close_from(6);
    #ifdef AFB_PRIVILEGED_CHANNEL_CONTROL
    if (privileged && !permanent_drop(uid, gid)) _exit(74);
    #else
    (void)privileged;
    #endif
    if (getuid() != uid || geteuid() != uid || getgid() != gid || getegid() != gid
        || write(5, "r", 1) != 1) _exit(74);
    close(5);
    char command;
    if (read(4, &command, 1) != 1 || command != 'g') _exit(72);
    close(4);
    if (chdir("/var/empty")) _exit(71);
    char *arguments[] = {(char *)application, "--channel", "3", "--fixture", (char *)url, NULL};
    char *environment[] = {"PATH=/usr/bin:/bin:/usr/sbin:/sbin", "LC_ALL=C", "HOME=/var/empty", "TMPDIR=/var/empty", NULL};
    execve(application, arguments, environment);
    _exit(73);
}

static void watchdog(struct child children[2], int cancellation, int acknowledgement)
{
    alarm(20);
    int cancel_copy = duplicate(cancellation), ready_copy = duplicate(acknowledgement);
    if (dup2(cancel_copy, 3) < 0 || dup2(ready_copy, 4) < 0) _exit(71);
    close(0); close(1); close(2); close_from(5);
    if (setsid() != getpid() || chdir("/var/empty")) _exit(71);
    signal(SIGINT, SIG_IGN); signal(SIGHUP, SIG_IGN); signal(SIGQUIT, SIG_IGN);
    if (write(4, "r", 1) != 1) _exit(71);
    close(4);
    struct pollfd item = {3, POLLIN, 0};
    int found = poll(&item, 1, 17000);
    char command = 0;
    if (found > 0 && read(3, &command, 1) == 1 && command == 'q') _exit(0);
    for (unsigned i = 0; i < 2; ++i) if (same_child(&children[i])) {
        kill(children[i].pid, SIGCONT);
        kill(children[i].pid, SIGTERM);
    }
    double deadline = now() + 1;
    while (now() < deadline) delay();
    for (unsigned i = 0; i < 2; ++i)
        if (same_child(&children[i])) kill(children[i].pid, SIGKILL);
    _exit(0);
}

static bool valid_url(const char *url)
{
    const char *prefix = "http://127.0.0.1:";
    if (strncmp(url, prefix, strlen(prefix))) return false;
    const char *port = url + strlen(prefix), *end = port;
    while (*end >= '0' && *end <= '9') ++end;
    if (end == port || end - port > 5 || strncmp(end, "/channel/", 9)) return false;
    unsigned long number = strtoul(port, NULL, 10);
    const char *nonce = end + 9;
    return number >= 1024 && number <= 65535 && strlen(nonce) == 16
        && strspn(nonce, "0123456789abcdef") == 16;
}

int main(int argc, char **argv)
{
    if (argc != 3 || !valid_url(argv[2])) return 64;
    bool privileged = false;
    uid_t uids[2] = {AFB_RESEARCH_UID, AFB_RESEARCH_UID};
    gid_t gids[2] = {getgid(), getgid()};
    #ifdef AFB_PRIVILEGED_CHANNEL_CONTROL
    privileged = !strcmp(argv[1], "--root-channel");
    if (privileged ? getuid() != 0 || geteuid() != 0 : getuid() != AFB_RESEARCH_UID || geteuid() != AFB_RESEARCH_UID) return 64;
    #else
    if (getuid() != AFB_RESEARCH_UID || geteuid() != AFB_RESEARCH_UID) return 64;
    #endif
    bool stalled = !strcmp(argv[1], "--stalled-control");
    bool deadline_control = !strcmp(argv[1], "--deadline-control");
    bool limit_control = !strcmp(argv[1], "--output-limit-control");
    if (!privileged && !stalled && !deadline_control && !limit_control && strcmp(argv[1], "--control")) return 64;
    sigset_t mask;
    sigemptyset(&mask);
    if (sigprocmask(SIG_SETMASK, &mask, NULL)) return 65;
    int signals[] = {SIGALRM, SIGCHLD, SIGINT, SIGTERM, SIGHUP, SIGQUIT};
    for (unsigned i = 0; i < sizeof(signals)/sizeof(signals[0]); ++i)
        if (signal(signals[i], SIG_DFL) == SIG_ERR) return 65;
    signal(SIGPIPE, SIG_IGN);
    alarm(24);
    struct rlimit core = {0, 0};
    if (setrlimit(RLIMIT_CORE, &core)) return 65;
    #ifdef AFB_PRIVILEGED_CHANNEL_CONTROL
    struct passwd *account = getpwnam("nobody");
    if (!account || account->pw_uid != (uid_t)-2 || account->pw_gid != (gid_t)-2 || !account->pw_dir
        || strcmp(account->pw_dir, "/var/empty")) return 65;
    if (privileged) { uids[0] = account->pw_uid; gids[0] = account->pw_gid; gids[1] = AFB_RESEARCH_GID; }
    #endif
    int stdout_flags = fcntl(1, F_GETFL);
    if (stdout_flags < 0 || fcntl(1, F_SETFL, stdout_flags | O_NONBLOCK)) return 65;
    char root[PATH_MAX], paths[2][PATH_MAX];
    if (snprintf(root, sizeof(root), "%s", __FILE__) >= (int)sizeof(root)) return 65;
    for (unsigned i = 0; i < 3; ++i) {
        char *end = strrchr(root, '/');
        if (!end) return 65;
        *end = 0;
    }
    #ifdef AFB_PRIVILEGED_CHANNEL_CONTROL
    const char *names[] = {"ChannelIsolatedRendererProbe", "ChannelIsolatedDisplayProbe"};
    if (privileged && !staged_paths(paths, names)) return 66;
    #else
    const char *names[] = {"ChannelRendererProbe", "ChannelDisplayProbe"};
    #endif
    for (unsigned i = 0; i < 2; ++i)
        if (!privileged && snprintf(paths[i], sizeof(paths[i]), "%s/dist/%s.app/Contents/MacOS/%s", root, names[i], names[i]) >= (int)sizeof(paths[i])) return 65;
    int pair[2] = {-1,-1}, output[2] = {-1,-1}, gates[2][2] = {{-1,-1},{-1,-1}};
    int child_ready[2][2] = {{-1,-1},{-1,-1}};
    int cancel[2] = {-1,-1}, armed[2] = {-1,-1};
    struct child children[2] = {{0},{0}}, guard = {0};
    bool complete = false, exceeded = false, timed_out = false, output_failed = false;
    bool cleanup = true, display_started = false, armed_guard = false;
    bool identities_checked = false, identity_violation = false, exec_observed[2] = {false,false};
    size_t total = 0, limit = limit_control ? 1024 : 384 * 1024;
    if (socketpair(AF_UNIX, SOCK_STREAM, 0, pair) || pipe(output) || pipe(gates[0]) || pipe(gates[1])
        || pipe(cancel) || pipe(armed) || pipe(child_ready[0]) || pipe(child_ready[1])) goto finish;
    unsigned char session[16];
    arc4random_buf(session, sizeof(session));
    for (unsigned i = 0; i < 2; ++i) {
        int size = 1024;
        if (setsockopt(pair[i], SOL_SOCKET, SO_SNDBUF, &size, sizeof(size))
            || send(pair[i], session, sizeof(session), 0) != sizeof(session)) goto finish;
    }
    for (unsigned i = 0; i < sizeof(session); ++i) ((volatile unsigned char *)session)[i] = 0;
    for (unsigned i = 0; i < 2; ++i) {
        children[i].pid = fork();
        if (!children[i].pid) execute(paths[i], argv[2], pair[i], output[1], gates[i][0], child_ready[i][1], privileged, uids[i], gids[i]);
        if (children[i].pid < 0) goto finish;
        close(child_ready[i][1]); child_ready[i][1] = -1;
        struct pollfd item = {child_ready[i][0], POLLIN, 0};
        char ready = 0;
        if (poll(&item, 1, 2000) <= 0 || read(child_ready[i][0], &ready, 1) != 1 || ready != 'r'
            || proc_pidinfo(children[i].pid, PROC_PIDTBSDINFO, 0,
            &children[i].identity, sizeof(children[i].identity)) != sizeof(children[i].identity)
            || children[i].identity.pbi_uid != uids[i] || children[i].identity.pbi_ruid != uids[i]
            || children[i].identity.pbi_svuid != uids[i] || children[i].identity.pbi_gid != gids[i]
            || children[i].identity.pbi_rgid != gids[i] || children[i].identity.pbi_svgid != gids[i]
            || !same_child(&children[i])) goto finish;
        close(gates[i][0]); gates[i][0] = -1;
    }
    identities_checked = true;
    guard.pid = fork();
    if (!guard.pid) watchdog(children, cancel[0], armed[1]);
    if (guard.pid < 0) goto finish;
    close(cancel[0]); cancel[0] = -1;
    close(armed[1]); armed[1] = -1;
    struct pollfd readiness = {armed[0], POLLIN, 0};
    char acknowledgement = 0;
    if (poll(&readiness, 1, 2000) <= 0 || read(armed[0], &acknowledgement, 1) != 1 || acknowledgement != 'r'
        || getsid(guard.pid) != guard.pid) goto finish;
    armed_guard = true;
    printf("CHANNEL_LAUNCHER_READY {\"rendererPID\":%d,\"displayPID\":%d,\"watchdogPID\":%d,\"ordinaryUID\":%u,\"rendererUID\":%u,\"displayUID\":%u,\"permanentDropChecked\":%s,\"rootRun\":%s}\n",
        children[0].pid, children[1].pid, guard.pid, (uid_t)AFB_RESEARCH_UID, uids[0], uids[1], privileged?"true":"false", privileged?"true":"false");
    fflush(stdout);
    close(pair[0]); pair[0] = -1; close(pair[1]); pair[1] = -1;
    close(output[1]); output[1] = -1;
    if (!stalled && write(gates[0][1], "g", 1) != 1) goto finish;
    char line[65537]; size_t line_length = 0;
    double deadline = now() + (stalled ? 3 : deadline_control ? 1 : 14);
    while (now() < deadline) {
        for (unsigned i = 0; i < 2; ++i) {
            char path[PROC_PIDPATHINFO_MAXSIZE];
            if (proc_pidpath(children[i].pid, path, sizeof(path)) > 0 && !strcmp(path, paths[i])) {
                if (!same_child(&children[i])) identity_violation = true;
                else exec_observed[i] = true;
            }
        }
        if (identity_violation) break;
        struct pollfd item = {output[0], POLLIN, 0};
        if (poll(&item, 1, 50) <= 0) continue;
        unsigned char block[8192];
        ssize_t count = read(output[0], block, sizeof(block));
        if (!count) { complete = true; break; }
        if (count < 0) { if (errno == EINTR) continue; break; }
        if ((size_t)count > limit - total) { exceeded = true; break; }
        total += count;
        for (ssize_t i = 0; i < count; ++i) {
            if (line_length >= sizeof(line)-1) { output_failed = true; break; }
            line[line_length++] = block[i];
            if (block[i] != '\n') continue;
            line[line_length] = 0;
            if (!display_started && !strncmp(line, "CHANNEL_RENDERER_READY ", 23)) {
                display_started = write(gates[1][1], "g", 1) == 1;
                if (!display_started) output_failed = true;
            }
            line_length = 0;
        }
        size_t offset = 0;
        double until = now() + 0.5;
        while (offset < (size_t)count && now() < until) {
            struct pollfd sink = {1, POLLOUT, 0};
            if (poll(&sink, 1, 25) <= 0) continue;
            ssize_t sent = write(1, block + offset, (size_t)count - offset);
            if (sent > 0) offset += sent;
            else if (sent < 0 && errno != EINTR && errno != EAGAIN) break;
        }
        if (offset != (size_t)count) output_failed = true;
        if (output_failed) break;
    }
    timed_out = !complete && !exceeded && !output_failed && now() >= deadline;
finish:
    for (unsigned i = 0; i < 2; ++i) cleanup = reap(&children[i], true) && cleanup;
    if (guard.pid > 1) {
        if (armed_guard && cleanup && cancel[1] >= 0) {
            if (write(cancel[1], "q", 1) != 1) cleanup = false;
            double deadline = now() + 1;
            while (!guard.reaped && now() < deadline) { reap(&guard, false); delay(); }
        }
        cleanup = reap(&guard, true) && cleanup;
    }
    int descriptors[] = {pair[0],pair[1],output[0],output[1],gates[0][0],gates[0][1],gates[1][0],gates[1][1],cancel[0],cancel[1],armed[0],armed[1],child_ready[0][0],child_ready[0][1],child_ready[1][0],child_ready[1][1]};
    for (unsigned i = 0; i < sizeof(descriptors)/sizeof(descriptors[0]); ++i) if (descriptors[i] >= 0) close(descriptors[i]);
    bool normal = true;
    for (unsigned i = 0; i < 2; ++i) normal = normal && children[i].reaped && WIFEXITED(children[i].status) && WEXITSTATUS(children[i].status) == 0;
    bool guard_normal = guard.reaped && WIFEXITED(guard.status) && WEXITSTATUS(guard.status) == 0;
    bool passed = complete && normal && guard_normal && cleanup && display_started && !exceeded && !output_failed
        && identities_checked && exec_observed[0] && exec_observed[1] && !identity_violation;
    printf("CHANNEL_LAUNCHER_IDENTITIES {\"initialKernelChecks\":%s,\"rendererPostExec\":%s,\"displayPostExec\":%s,\"identityViolation\":%s,\"rootRun\":%s}\n",
        identities_checked?"true":"false",exec_observed[0]?"true":"false",exec_observed[1]?"true":"false",identity_violation?"true":"false",privileged?"true":"false");
    printf("\nCHANNEL_LAUNCHER_RESULT {\"passed\":%s,\"cleanupVerified\":%s,\"rendererReaped\":%s,\"displayReaped\":%s,\"watchdogReaped\":%s,\"watchdogNormalExit\":%s,\"displayStartedAfterRendererReady\":%s,\"outputLimitExceeded\":%s,\"deadlineReached\":%s,\"outputFailed\":%s,\"bytesRelayed\":%zu,\"rootRun\":%s}\n",
        passed?"true":"false",cleanup?"true":"false",children[0].reaped?"true":"false",children[1].reaped?"true":"false",guard.reaped?"true":"false",guard_normal?"true":"false",display_started?"true":"false",exceeded?"true":"false",timed_out?"true":"false",output_failed?"true":"false",total,privileged?"true":"false");
    fflush(stdout);
    fcntl(1, F_SETFL, stdout_flags);
    alarm(0);
    return passed ? 0 : 1;
}

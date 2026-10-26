#include <errno.h>
#include <fcntl.h>
#include <libproc.h>
#include <limits.h>
#include <mach-o/dyld.h>
#include <poll.h>
#include <pwd.h>
#include <signal.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#if !defined(AFB_RESEARCH_UID) || !defined(AFB_RESEARCH_GID)
#error Compile this diagnostic with the ordinary research identity.
#endif

enum mode { SMOKE, WATCHDOG_CONTROL, LIMIT_CONTROL, DEADLINE_CONTROL };
struct readiness { unsigned magic; bool permanent_drop; };
struct owned_child { pid_t pid; bool reaped; int status; };
static const size_t output_limit = 3 * 1024 * 1024;

static double now(void)
{
    struct timespec t;
    if (clock_gettime(CLOCK_MONOTONIC, &t))
        _exit(3);
    return t.tv_sec + t.tv_nsec / 1e9;
}

static void delay(unsigned milliseconds)
{
    struct timespec interval = { milliseconds / 1000, (milliseconds % 1000) * 1000000 };
    while (nanosleep(&interval, &interval) && errno == EINTR) { }
}

static bool normalize_signals(void)
{
    struct sigaction action = { 0 };
    action.sa_handler = SIG_DFL;
    sigemptyset(&action.sa_mask);
    int signals[] = { SIGALRM, SIGCHLD, SIGINT, SIGTERM, SIGHUP, SIGQUIT, SIGPIPE };
    for (size_t i = 0; i < sizeof(signals) / sizeof(signals[0]); ++i)
        if (sigaction(signals[i], &action, NULL))
            return false;
    sigset_t mask;
    sigemptyset(&mask);
    return sigprocmask(SIG_SETMASK, &mask, NULL) == 0;
}

static bool credentials(pid_t pid, uid_t uid, gid_t gid, struct proc_bsdinfo *info)
{
    return proc_pidinfo(pid, PROC_PIDTBSDINFO, 0, info, sizeof(*info)) == sizeof(*info)
        && info->pbi_ruid == uid && info->pbi_uid == uid && info->pbi_svuid == uid
        && info->pbi_rgid == gid && info->pbi_gid == gid && info->pbi_svgid == gid;
}

static bool permanent_drop(uid_t uid, gid_t gid)
{
    if (!uid || !gid || setgroups(1, &gid) || setgid(gid) || setuid(uid))
        return false;
    struct proc_bsdinfo info;
    gid_t groups[64];
    int count = getgroups(64, groups);
    if (!credentials(getpid(), uid, gid, &info) || count != 1 || groups[0] != gid)
        return false;
    errno = 0;
    if (setuid(0) != -1 || errno != EPERM)
        return false;
    errno = 0;
    return setgid(0) == -1 && errno == EPERM;
}

static void close_except(int first, int second)
{
    int maximum = getdtablesize();
    for (int fd = 0; fd < maximum; ++fd)
        if (fd != first && fd != second)
            close(fd);
}

static bool receive(int fd, void *buffer, size_t length, unsigned timeout)
{
    struct pollfd item = { fd, POLLIN, 0 };
    return poll(&item, 1, (int)timeout) > 0 && read(fd, buffer, length) == (ssize_t)length;
}

static bool same_identity(pid_t pid, const struct proc_bsdinfo *identity)
{
    struct proc_bsdinfo current;
    return pid > 1 && proc_pidinfo(pid, PROC_PIDTBSDINFO, 0, &current, sizeof(current)) == sizeof(current)
        && current.pbi_start_tvsec == identity->pbi_start_tvsec
        && current.pbi_start_tvusec == identity->pbi_start_tvusec
        && current.pbi_uid == identity->pbi_uid && current.pbi_ruid == identity->pbi_ruid
        && current.pbi_svuid == identity->pbi_svuid;
}

static bool reap(struct owned_child *child)
{
    if (child->pid <= 1 || child->reaped)
        return true;
    pid_t found;
    do { found = waitpid(child->pid, &child->status, WNOHANG); } while (found < 0 && errno == EINTR);
    if (found == child->pid) {
        child->reaped = true;
        return true;
    }
    if (found < 0) {
        child->reaped = errno == ECHILD;
        return false;
    }
    // This child remains unreaped, so its fork-created PID cannot be reused.
    kill(child->pid, SIGCONT);
    kill(child->pid, SIGTERM);
    double deadline = now() + 1;
    while (now() < deadline) {
        found = waitpid(child->pid, &child->status, WNOHANG);
        if (found == child->pid) {
            child->reaped = true;
            return true;
        }
        if (found < 0 && errno != EINTR) {
            child->reaped = errno == ECHILD;
            return false;
        }
        delay(10);
    }
    kill(child->pid, SIGKILL);
    deadline = now() + 1;
    while (now() < deadline) {
        found = waitpid(child->pid, &child->status, WNOHANG);
        if (found == child->pid) {
            child->reaped = true;
            return true;
        }
        if (found < 0 && errno != EINTR) {
            child->reaped = errno == ECHILD;
            return false;
        }
        delay(10);
    }
    return false;
}

static bool wait_owned(struct owned_child *child, unsigned milliseconds)
{
    if (child->pid <= 1 || child->reaped)
        return true;
    double deadline = now() + milliseconds / 1000.0;
    do {
        pid_t found = waitpid(child->pid, &child->status, WNOHANG);
        if (found == child->pid) {
            child->reaped = true;
            return true;
        }
        if (found < 0 && errno != EINTR) {
            child->reaped = errno == ECHILD;
            return false;
        }
        if (now() >= deadline)
            break;
        delay(10);
    } while (true);
    return false;
}

static bool protected_path(const char *path, mode_t mode, bool directory)
{
    struct stat st;
    return lstat(path, &st) == 0 && st.st_uid == 0 && (st.st_mode & 07777) == mode
        && (directory ? S_ISDIR(st.st_mode) : S_ISREG(st.st_mode) && st.st_nlink == 1);
}

static bool root_stage(char *application, size_t capacity)
{
    char executable[PATH_MAX], resolved[PATH_MAX];
    uint32_t length = sizeof(executable);
    if (_NSGetExecutablePath(executable, &length) || !realpath(executable, resolved)
        || !protected_path(resolved, 0700, false))
        return false;
    char *name = strrchr(resolved, '/');
    if (!name || strcmp(name, "/renderer-identity-supervisor"))
        return false;
    *name = 0;
    const char *prefix = "/private/tmp/agentfreebrowser-renderer.";
    if (strncmp(resolved, prefix, strlen(prefix)) || !resolved[strlen(prefix)]
        || strchr(resolved + strlen(prefix), '/') || !protected_path(resolved, 0711, true))
        return false;
    const char *suffixes[] = {
        "/RendererIdentityProbe.app", "/RendererIdentityProbe.app/Contents",
        "/RendererIdentityProbe.app/Contents/MacOS", "/RendererIdentityProbe.app/Contents/_CodeSignature",
        "/RendererIdentityProbe.app/Contents/Info.plist", "/RendererIdentityProbe.app/Contents/_CodeSignature/CodeResources",
        "/RendererIdentityProbe.app/Contents/MacOS/RendererIdentityProbe"
    };
    for (size_t i = 0; i < sizeof(suffixes) / sizeof(suffixes[0]); ++i) {
        char path[PATH_MAX];
        int count = snprintf(path, sizeof(path), "%s%s", resolved, suffixes[i]);
        if (count < 0 || count >= (int)sizeof(path)
            || !protected_path(path, i < 4 || i == 6 ? 0555 : 0444, i < 4))
            return false;
    }
    int count = snprintf(application, capacity, "%s%s", resolved, suffixes[6]);
    return count > 0 && count < (int)capacity;
}

static bool local_application(char *application, size_t capacity)
{
    char root[PATH_MAX];
    if (snprintf(root, sizeof(root), "%s", __FILE__) >= (int)sizeof(root))
        return false;
    for (unsigned i = 0; i < 3; ++i) {
        char *end = strrchr(root, '/');
        if (!end)
            return false;
        *end = 0;
    }
    int count = snprintf(application, capacity, "%s/dist/RendererIdentityProbe.app/Contents/MacOS/RendererIdentityProbe", root);
    return count > 0 && count < (int)capacity;
}

static void watchdog(pid_t target, struct proc_bsdinfo identity, int cancel, int ready, unsigned seconds)
{
    alarm(31);
    close_except(cancel, ready);
    if (setsid() != getpid() || chdir("/var/empty"))
        _exit(4);
    signal(SIGINT, SIG_IGN);
    signal(SIGHUP, SIG_IGN);
    signal(SIGQUIT, SIG_IGN);
    if (write(ready, "r", 1) != 1)
        _exit(4);
    close(ready);
    struct pollfd item = { cancel, POLLIN, 0 };
    int found = poll(&item, 1, (int)(seconds * 1000));
    char command = 0;
    if (found > 0 && read(cancel, &command, 1) == 1 && command == 'q')
        _exit(0);
    if (same_identity(target, &identity)) {
        kill(target, SIGCONT);
        kill(target, SIGTERM);
        delay(1000);
        if (same_identity(target, &identity))
            kill(target, SIGKILL);
    }
    _exit(0);
}

static bool relay(int fd, const unsigned char *bytes, size_t length)
{
    double deadline = now() + 1;
    while (length && now() < deadline) {
        struct pollfd item = { fd, POLLOUT, 0 };
        if (poll(&item, 1, 100) <= 0)
            continue;
        size_t portion = length > _POSIX_PIPE_BUF ? _POSIX_PIPE_BUF : length;
        ssize_t count = write(fd, bytes, portion);
        if (count > 0) {
            bytes += count;
            length -= (size_t)count;
        } else if (count < 0 && errno != EINTR && errno != EAGAIN)
            return false;
    }
    return length == 0;
}

static int run(enum mode mode, bool privileged, uid_t uid, gid_t gid, const char *application)
{
    int output[2] = {-1, -1}, ready[2] = {-1, -1}, gate[2] = {-1, -1};
    int cancellation[2] = {-1, -1}, armed[2] = {-1, -1};
    struct owned_child host = { 0 }, guard = { 0 };
    struct proc_bsdinfo identity = { 0 };
    bool cleanup = true, watchdog_armed = false, identity_checked = false;
    bool eof = false, exceeded = false, timed_out = false, delivered = true;
    bool post_exec_identity = false, identity_violation = false;
    size_t total = 0;
    if (pipe(output) || pipe(ready) || pipe(gate))
        goto finish;
    host.pid = fork();
    if (host.pid == 0) {
        alarm(25);
        close(output[0]); close(ready[0]); close(gate[1]);
        for (int fd = 3, maximum = getdtablesize(); fd < maximum; ++fd)
            if (fd != output[1] && fd != ready[1] && fd != gate[0])
                close(fd);
        signal(SIGPIPE, SIG_DFL);
        if (privileged && !permanent_drop(uid, gid))
            _exit(4);
        struct readiness message = { 0x41464231, privileged };
        if (write(ready[1], &message, sizeof(message)) != sizeof(message))
            _exit(4);
        close(ready[1]);
        char command = 0;
        if (!receive(gate[0], &command, 1, 3000) || command != 'g')
            _exit(4);
        close(gate[0]);
        if (dup2(output[1], STDOUT_FILENO) < 0 || dup2(output[1], STDERR_FILENO) < 0)
            _exit(4);
        int null = open("/dev/null", O_RDONLY | O_NOFOLLOW);
        if (null < 0 || dup2(null, STDIN_FILENO) < 0)
            _exit(4);
        for (int fd = 3, maximum = getdtablesize(); fd < maximum; ++fd)
            close(fd);
        if (chdir("/var/empty"))
            _exit(4);
        if (mode == LIMIT_CONTROL) {
            unsigned char block[4096];
            memset(block, 'a', sizeof(block));
            for (;;) {
                if (write(STDOUT_FILENO, block, sizeof(block)) <= 0)
                    _exit(4);
            }
        }
        if (mode != SMOKE) {
            for (;;) pause();
        }
        char *args[] = { (char *)application, "--pipe-only", NULL };
        char *environment[] = { "PATH=/usr/bin:/bin:/usr/sbin:/sbin", "LC_ALL=C", "HOME=/var/empty", "TMPDIR=/var/empty", NULL };
        execve(application, args, environment);
        _exit(5);
    }
    if (host.pid < 0)
        goto finish;
    close(output[1]); output[1] = -1;
    close(ready[1]); ready[1] = -1;
    close(gate[0]); gate[0] = -1;
    struct readiness message = { 0 };
    if (!receive(ready[0], &message, sizeof(message), 2000) || message.magic != 0x41464231
        || message.permanent_drop != privileged || !credentials(host.pid, uid, gid, &identity))
        goto finish;
    identity_checked = true;
    if (pipe(cancellation) || pipe(armed))
        goto finish;
    guard.pid = fork();
    if (guard.pid == 0)
        watchdog(host.pid, identity, cancellation[0], armed[1], mode == WATCHDOG_CONTROL ? 3 : 28);
    if (guard.pid < 0)
        goto finish;
    close(cancellation[0]); cancellation[0] = -1;
    close(armed[1]); armed[1] = -1;
    char acknowledgement = 0;
    if (!receive(armed[0], &acknowledgement, 1, 1000) || acknowledgement != 'r'
        || getsid(guard.pid) != guard.pid || getpgid(guard.pid) != guard.pid)
        goto finish;
    watchdog_armed = true;
    printf("SUPERVISOR_READY {\"hostPID\":%d,\"watchdogPID\":%d,\"uid\":%u,\"gid\":%u,\"permanentDropChecked\":%s,\"kernelIdentityChecked\":true,\"watchdogDetached\":true}\n",
        host.pid, guard.pid, uid, gid, privileged ? "true" : "false");
    if (write(gate[1], "g", 1) != 1)
        goto finish;
    close(gate[1]); gate[1] = -1;
    if (mode == WATCHDOG_CONTROL) {
        if (kill(host.pid, SIGSTOP))
            goto finish;
        int stopped = 0;
        pid_t found;
        do { found = waitpid(host.pid, &stopped, WUNTRACED); } while (found < 0 && errno == EINTR);
        if (found != host.pid || !WIFSTOPPED(stopped))
            goto finish;
        printf("SUPERVISOR_STOPPED {\"hostPID\":%d,\"watchdogPID\":%d,\"stopped\":true}\n", host.pid, guard.pid);
    }
    double deadline = now() + (mode == DEADLINE_CONTROL ? 3 : 22);
    while (now() < deadline) {
        if (mode == SMOKE) {
            char path[PROC_PIDPATHINFO_MAXSIZE];
            struct proc_bsdinfo current;
            if (proc_pidpath(host.pid, path, sizeof(path)) > 0 && !strcmp(path, application)) {
                if (!credentials(host.pid, uid, gid, &current)
                    || current.pbi_start_tvsec != identity.pbi_start_tvsec
                    || current.pbi_start_tvusec != identity.pbi_start_tvusec) {
                    identity_violation = true;
                    break;
                }
                post_exec_identity = true;
            }
        }
        struct pollfd item = { output[0], POLLIN, 0 };
        int found = poll(&item, 1, 100);
        if (found < 0 && errno != EINTR)
            break;
        if (found <= 0)
            continue;
        unsigned char block[8192];
        ssize_t count = read(output[0], block, sizeof(block));
        if (!count) { eof = true; break; }
        if (count < 0) { if (errno == EINTR) continue; break; }
        if ((size_t)count > output_limit - total) { exceeded = true; break; }
        total += (size_t)count;
        if (!relay(STDOUT_FILENO, block, (size_t)count)) { delivered = false; break; }
    }
    timed_out = !eof && !exceeded && delivered && now() >= deadline;
finish:
    signal(SIGPIPE, SIG_IGN);
    if (eof)
        wait_owned(&host, 500);
    cleanup = reap(&host) && cleanup;
    if (!host.reaped && cancellation[1] >= 0) {
        close(cancellation[1]); cancellation[1] = -1;
        wait_owned(&host, 2500);
    }
    if (guard.pid > 1) {
        wait_owned(&guard, 0);
        if (host.reaped && !guard.reaped && cancellation[1] >= 0
            && write(cancellation[1], "q", 1) != 1 && errno != EPIPE)
            cleanup = false;
        if (!wait_owned(&guard, 1500) && host.reaped)
            cleanup = reap(&guard) && cleanup;
    }
    cleanup = host.reaped && guard.reaped && cleanup;
    int descriptors[] = { output[0], output[1], ready[0], ready[1], gate[0], gate[1], cancellation[0], cancellation[1], armed[0], armed[1] };
    for (size_t i = 0; i < sizeof(descriptors) / sizeof(descriptors[0]); ++i)
        if (descriptors[i] >= 0)
            close(descriptors[i]);
    bool normal = host.reaped && WIFEXITED(host.status) && WEXITSTATUS(host.status) == 0;
    bool guard_normal = guard.reaped && WIFEXITED(guard.status) && WEXITSTATUS(guard.status) == 0;
    bool passed = identity_checked && post_exec_identity && !identity_violation && watchdog_armed && cleanup && guard_normal && delivered && eof && normal;
    printf("\nSUPERVISOR_RESULT {\"scope\":\"transport-and-own-child-lifecycle\",\"mode\":%d,\"privileged\":%s,\"hostPID\":%d,\"watchdogPID\":%d,\"bytesRelayed\":%zu,\"outputLimitExceeded\":%s,\"deadlineReached\":%s,\"pipeEOF\":%s,\"hostReaped\":%s,\"watchdogReaped\":%s,\"watchdogNormalExit\":%s,\"postExecIdentityObserved\":%s,\"identityViolation\":%s,\"hostExitCode\":%d,\"hostSignal\":%d,\"cleanupVerified\":%s,\"passed\":%s}\n",
        mode, privileged ? "true" : "false", host.pid, guard.pid, total, exceeded ? "true" : "false",
        timed_out ? "true" : "false", eof ? "true" : "false", host.reaped ? "true" : "false", guard.reaped ? "true" : "false", guard_normal ? "true" : "false",
        post_exec_identity ? "true" : "false", identity_violation ? "true" : "false",
        host.reaped && WIFEXITED(host.status) ? WEXITSTATUS(host.status) : -1,
        host.reaped && WIFSIGNALED(host.status) ? WTERMSIG(host.status) : 0,
        cleanup ? "true" : "false", passed ? "true" : "false");
    return passed ? 0 : 1;
}

int main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    if (argc != 2)
        return 64;
    bool privileged = !strcmp(argv[1], "--root-smoke");
    bool preflight = !strcmp(argv[1], "--preflight");
    enum mode mode = SMOKE;
    if (!strcmp(argv[1], "--watchdog-control")) mode = WATCHDOG_CONTROL;
    else if (!strcmp(argv[1], "--output-limit-control")) mode = LIMIT_CONTROL;
    else if (!strcmp(argv[1], "--deadline-control")) mode = DEADLINE_CONTROL;
    else if (!privileged && !preflight && strcmp(argv[1], "--same-user-control")) return 64;
    if (privileged ? getuid() != 0 || geteuid() != 0 : getuid() != AFB_RESEARCH_UID || geteuid() != AFB_RESEARCH_UID)
        return 64;
    if (!normalize_signals())
        return 67;
    alarm(32);
    struct rlimit core = { 0, 0 };
    if (setrlimit(RLIMIT_CORE, &core))
        return 67;
    struct passwd *account = getpwnam("nobody");
    bool valid_account = account && account->pw_uid != 0 && account->pw_gid != 0
        && account->pw_uid != AFB_RESEARCH_UID && account->pw_dir && !strcmp(account->pw_dir, "/var/empty");
    uid_t uid = privileged && valid_account ? account->pw_uid : AFB_RESEARCH_UID;
    gid_t gid = privileged && valid_account ? account->pw_gid : AFB_RESEARCH_GID;
    struct stat empty;
    if (!valid_account || lstat("/var/empty", &empty) || !S_ISDIR(empty.st_mode)
        || empty.st_uid != 0 || empty.st_mode & 0022)
        return 65;
    if (preflight) {
        printf("{\"compiledUID\":%u,\"compiledGID\":%u,\"isolatedUID\":%u,\"isolatedGID\":%u,\"isolatedHome\":\"/var/empty\",\"effectiveUID\":%u,\"accountValid\":true,\"rootRun\":false}\n",
            (uid_t)AFB_RESEARCH_UID, (gid_t)AFB_RESEARCH_GID, account->pw_uid, account->pw_gid, geteuid());
        alarm(0);
        return 0;
    }
    char application[PATH_MAX];
    if (privileged ? !root_stage(application, sizeof(application)) : !local_application(application, sizeof(application)))
        return 66;
    if (fcntl(STDOUT_FILENO, F_GETFL) < 0)
        return 67;
    int result = run(mode, privileged, uid, gid, application);
    alarm(0);
    return result;
}

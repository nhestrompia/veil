#include <errno.h>
#include <libproc.h>
#include <mach-o/dyld.h>
#include <poll.h>
#include <pwd.h>
#include <signal.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#ifndef AFB_RESEARCH_UID
#error Compile this diagnostic with the invoking research identity.
#endif
#ifndef AFB_RESEARCH_GID
#error Compile this diagnostic with the invoking research group.
#endif

struct reply {
    int kind;
    int result;
    int error;
    int groups_valid;
    int root_regain_denied;
    double timestamp;
};

struct child {
    pid_t pid;
    bool reaped;
};

static double now(void)
{
    struct timespec value;
    if (clock_gettime(CLOCK_MONOTONIC, &value))
        _exit(3);
    return value.tv_sec + value.tv_nsec / 1e9;
}

static void delay(unsigned milliseconds)
{
    struct timespec interval = { milliseconds / 1000, (milliseconds % 1000) * 1000000 };
    while (nanosleep(&interval, &interval) && errno == EINTR) { }
}

static bool read_reply(int fd, struct reply *value)
{
    struct pollfd item = { fd, POLLIN, 0 };
    return poll(&item, 1, 1000) > 0 && read(fd, value, sizeof(*value)) == sizeof(*value);
}

static bool write_reply(int fd, struct reply value)
{
    return write(fd, &value, sizeof(value)) == sizeof(value);
}

static bool credentials(pid_t pid, uid_t uid, gid_t gid, struct proc_bsdinfo *info)
{
    return proc_pidinfo(pid, PROC_PIDTBSDINFO, 0, info, sizeof(*info)) == sizeof(*info)
        && info->pbi_uid == uid && info->pbi_ruid == uid && info->pbi_svuid == uid
        && info->pbi_gid == gid && info->pbi_rgid == gid && info->pbi_svgid == gid;
}

static bool permanent_drop(uid_t uid, gid_t gid)
{
    if (uid == 0 || gid == 0 || setgroups(1, &gid) || setgid(gid) || setuid(uid))
        return false;
    struct proc_bsdinfo info;
    gid_t groups[64];
    int count = getgroups(64, groups);
    if (!credentials(getpid(), uid, gid, &info) || count < 1)
        return false;
    for (int index = 0; index < count; ++index)
        if (groups[index] != gid)
            return false;
    errno = 0;
    if (setuid(0) != -1 || errno != EPERM)
        return false;
    errno = 0;
    return setgid(0) == -1 && errno == EPERM;
}

static bool same_child(pid_t pid, const struct proc_bsdinfo *identity)
{
    struct proc_bsdinfo current;
    return pid > 1 && proc_pidinfo(pid, PROC_PIDTBSDINFO, 0, &current, sizeof(current)) == sizeof(current)
        && current.pbi_start_tvsec == identity->pbi_start_tvsec
        && current.pbi_start_tvusec == identity->pbi_start_tvusec
        && current.pbi_uid == identity->pbi_uid && current.pbi_ruid == identity->pbi_ruid
        && current.pbi_svuid == identity->pbi_svuid;
}

static bool reap(struct child *child)
{
    if (child->pid <= 1 || child->reaped)
        return true;
    int status;
    pid_t observed;
    do { observed = waitpid(child->pid, &status, WNOHANG); } while (observed < 0 && errno == EINTR);
    if (observed == child->pid) {
        child->reaped = true;
        return true;
    }
    if (observed < 0) {
        child->reaped = errno == ECHILD;
        return false;
    }
    // Each PID comes from fork and remains unreaped. The kernel cannot reuse it.
    kill(child->pid, SIGCONT);
    kill(child->pid, SIGTERM);
    double deadline = now() + 1;
    while (now() < deadline) {
        observed = waitpid(child->pid, &status, WNOHANG);
        if (observed == child->pid) {
            child->reaped = true;
            return true;
        }
        if (observed < 0 && errno != EINTR) {
            child->reaped = errno == ECHILD;
            return false;
        }
        delay(10);
    }
    kill(child->pid, SIGKILL);
    deadline = now() + 1;
    while (now() < deadline) {
        observed = waitpid(child->pid, &status, WNOHANG);
        if (observed == child->pid) {
            child->reaped = true;
            return true;
        }
        if (observed < 0 && errno != EINTR) {
            child->reaped = errno == ECHILD;
            return false;
        }
        delay(10);
    }
    return false;
}

static bool root_staged(void)
{
    char raw[4096], resolved[4096];
    uint32_t size = sizeof(raw);
    struct stat file, directory;
    if (_NSGetExecutablePath(raw, &size) || !realpath(raw, resolved))
        return false;
    const char *prefix = "/private/tmp/agentfreebrowser-identity.";
    char *name = strrchr(resolved, '/');
    if (!name || strcmp(name, "/identity-signal-control") || strncmp(resolved, prefix, strlen(prefix)))
        return false;
    if (lstat(resolved, &file) || !S_ISREG(file.st_mode) || file.st_uid != 0
        || (file.st_mode & 07777) != 0700 || file.st_nlink != 1)
        return false;
    *name = 0;
    return strchr(resolved + strlen(prefix), '/') == NULL && lstat(resolved, &directory) == 0
        && S_ISDIR(directory.st_mode) && directory.st_uid == 0 && (directory.st_mode & 07777) == 0700;
}

static bool normalize_signals(void)
{
    struct sigaction action = {0};
    action.sa_handler = SIG_DFL;
    sigemptyset(&action.sa_mask);
    int signals[] = {SIGALRM, SIGCHLD, SIGINT, SIGTERM, SIGHUP, SIGQUIT};
    for (unsigned index = 0; index < sizeof(signals) / sizeof(signals[0]); ++index)
        if (sigaction(signals[index], &action, NULL)) return false;
    sigset_t empty;
    sigemptyset(&empty);
    return sigprocmask(SIG_SETMASK, &empty, NULL) == 0;
}

static bool trial(uid_t target_uid, gid_t target_gid, bool privileged, bool recovery, const char *name)
{
    int replies[2] = {-1, -1}, commands[2] = {-1, -1};
    int actor_replies[2] = {-1, -1}, actor_commands[2] = {-1, -1};
    int watchdog_ready[2] = {-1, -1};
    struct child target = {0}, actor = {0}, watchdog = {0};
    struct reply ready = {0}, sent = {0}, heartbeat = {0}, monitor = {0};
    struct proc_bsdinfo target_identity = {0}, actor_identity = {0};
    bool valid = false, stopped = false, continued = false, alive = false, cleanup = true, drops_checked = false;
    bool detached = false;
    double heartbeat_elapsed = -1;
    bool expect_allowed = target_uid == (uid_t)AFB_RESEARCH_UID;
    if (pipe(replies) || pipe(commands))
        goto finish;
    target.pid = fork();
    if (target.pid == 0) {
        alarm(8);
        close(replies[0]); close(commands[1]);
        if (privileged && !permanent_drop(target_uid, target_gid))
            _exit(4);
        if (!write_reply(replies[1], (struct reply){.kind = 1, .groups_valid = privileged, .root_regain_denied = privileged}))
            _exit(4);
        char command;
        while (read(commands[0], &command, 1) == 1) {
            if (command != 'p' || !write_reply(replies[1], (struct reply){.kind = 2}))
                _exit(4);
        }
        _exit(0);
    }
    if (target.pid < 0)
        goto finish;
    close(replies[1]); replies[1] = -1;
    close(commands[0]); commands[0] = -1;
    if (!read_reply(replies[0], &ready) || ready.kind != 1
        || !credentials(target.pid, target_uid, target_gid, &target_identity)
        || target_identity.pbi_ppid != (uint32_t)getpid())
        goto finish;
    if (pipe(watchdog_ready))
        goto finish;
    watchdog.pid = fork();
    if (watchdog.pid == 0) {
        alarm(8);
        close(replies[0]); close(commands[1]);
        close(watchdog_ready[0]);
        if (setsid() != getpid())
            _exit(4);
        signal(SIGINT, SIG_IGN); signal(SIGHUP, SIG_IGN); signal(SIGQUIT, SIG_IGN);
        if (!write_reply(watchdog_ready[1], (struct reply){.kind = 5, .timestamp = now()}))
            _exit(4);
        close(watchdog_ready[1]);
        close(STDIN_FILENO); close(STDOUT_FILENO); close(STDERR_FILENO);
        delay(2000);
        if (same_child(target.pid, &target_identity))
            kill(target.pid, SIGCONT);
        delay(4000);
        if (same_child(target.pid, &target_identity)) {
            kill(target.pid, SIGCONT);
            kill(target.pid, SIGTERM);
        }
        _exit(0);
    }
    if (watchdog.pid < 0)
        goto finish;
    close(watchdog_ready[1]); watchdog_ready[1] = -1;
    if (!read_reply(watchdog_ready[0], &monitor) || monitor.kind != 5
        || getsid(watchdog.pid) != watchdog.pid || getpgid(watchdog.pid) != watchdog.pid)
        goto finish;
    detached = true;
    close(watchdog_ready[0]); watchdog_ready[0] = -1;
    if (pipe(actor_replies) || pipe(actor_commands))
        goto finish;
    actor.pid = fork();
    if (actor.pid == 0) {
        alarm(8);
        close(replies[0]); close(commands[1]);
        close(actor_replies[0]); close(actor_commands[1]);
        if (privileged && !permanent_drop(AFB_RESEARCH_UID, AFB_RESEARCH_GID))
            _exit(4);
        if (!write_reply(actor_replies[1], (struct reply){.kind = 3, .groups_valid = privileged, .root_regain_denied = privileged}))
            _exit(4);
        char command;
        if (read(actor_commands[0], &command, 1) != 1 || command != 's')
            _exit(4);
        errno = 0;
        int status = kill(target.pid, SIGSTOP);
        int error = errno;
        if (!write_reply(actor_replies[1], (struct reply){.kind = 4, .result = status, .error = error}))
            _exit(4);
        read(actor_commands[0], &command, 1);
        _exit(0);
    }
    if (actor.pid < 0)
        goto finish;
    close(actor_replies[1]); actor_replies[1] = -1;
    close(actor_commands[0]); actor_commands[0] = -1;
    struct reply actor_ready;
    if (!read_reply(actor_replies[0], &actor_ready) || actor_ready.kind != 3
        || !credentials(actor.pid, AFB_RESEARCH_UID, AFB_RESEARCH_GID, &actor_identity)
        || actor_identity.pbi_ppid != (uint32_t)getpid()
        || (privileged && (!ready.groups_valid || !ready.root_regain_denied
            || !actor_ready.groups_valid || !actor_ready.root_regain_denied)))
        goto finish;
    drops_checked = privileged;
    if (!same_child(target.pid, &target_identity) || write(actor_commands[1], "s", 1) != 1
        || !read_reply(actor_replies[0], &sent) || sent.kind != 4)
        goto finish;
    double deadline = now() + (expect_allowed ? 0.5 : 0.1);
    while (now() < deadline) {
        int status;
        pid_t observed = waitpid(target.pid, &status, WNOHANG | WUNTRACED);
        if (observed == target.pid) {
            if (WIFEXITED(status) || WIFSIGNALED(status)) {
                target.reaped = true;
                goto finish;
            }
            stopped = WIFSTOPPED(status) && WSTOPSIG(status) == SIGSTOP;
            break;
        }
        delay(10);
    }
    if (!same_child(target.pid, &target_identity))
        goto finish;
    if (recovery) {
        printf("{\"stage\":\"stopped-control\",\"targetPID\":%d,\"actorPID\":%d,\"watchdogPID\":%d,\"watchdogDetached\":%s}\n",
               target.pid, actor.pid, watchdog.pid, detached ? "true" : "false");
        delay(2300);
    } else if (expect_allowed) {
        continued = kill(target.pid, SIGCONT) == 0;
    }
    alive = write(commands[1], "p", 1) == 1 && read_reply(replies[0], &heartbeat) && heartbeat.kind == 2;
    heartbeat_elapsed = now() - monitor.timestamp;
    valid = alive && (expect_allowed ? sent.result == 0 && stopped && (recovery || continued)
                                    : sent.result == -1 && sent.error == EPERM && !stopped && heartbeat_elapsed < 1.5);
finish:
    cleanup = reap(&actor) && cleanup;
    cleanup = reap(&target) && cleanup;
    cleanup = reap(&watchdog) && cleanup;
    int descriptors[] = {replies[0], replies[1], commands[0], commands[1], actor_replies[0], actor_replies[1], actor_commands[0], actor_commands[1], watchdog_ready[0], watchdog_ready[1]};
    for (unsigned index = 0; index < sizeof(descriptors) / sizeof(descriptors[0]); ++index)
        if (descriptors[index] >= 0) close(descriptors[index]);
    printf("{\"case\":\"%s\",\"targetUID\":%u,\"actorUID\":%u,\"targetPID\":%d,\"actorPID\":%d,\"targetRealUID\":%u,\"targetEffectiveUID\":%u,\"targetSavedUID\":%u,\"actorRealUID\":%u,\"actorEffectiveUID\":%u,\"actorSavedUID\":%u,\"targetRealGID\":%u,\"targetEffectiveGID\":%u,\"targetSavedGID\":%u,\"actorRealGID\":%u,\"actorEffectiveGID\":%u,\"actorSavedGID\":%u,\"permanentDropChecks\":%s,\"signalReturn\":%d,\"signalErrno\":%d,\"stopObserved\":%s,\"continued\":%s,\"heartbeat\":%s,\"heartbeatAfterWatchdogArmedSeconds\":%.6f,\"watchdogDetached\":%s,\"watchdogRecoveryControl\":%s,\"cleanupVerified\":%s,\"passed\":%s}\n",
           name, target_uid, (uid_t)AFB_RESEARCH_UID, target.pid, actor.pid,
           target_identity.pbi_ruid, target_identity.pbi_uid, target_identity.pbi_svuid,
           actor_identity.pbi_ruid, actor_identity.pbi_uid, actor_identity.pbi_svuid,
           target_identity.pbi_rgid, target_identity.pbi_gid, target_identity.pbi_svgid,
           actor_identity.pbi_rgid, actor_identity.pbi_gid, actor_identity.pbi_svgid,
           drops_checked ? "true" : "false",
           sent.result, sent.error, stopped ? "true" : "false", continued ? "true" : "false",
           alive ? "true" : "false", heartbeat_elapsed, detached ? "true" : "false", recovery ? "true" : "false",
           cleanup ? "true" : "false", valid && cleanup ? "true" : "false");
    return valid && cleanup;
}

int main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    if (argc != 2 || (strcmp(argv[1], "--preflight") && strcmp(argv[1], "--same-user-control") && strcmp(argv[1], "--same-user-watchdog-control") && strcmp(argv[1], "--root-experiment"))) {
        puts("{\"status\":\"refused\",\"reason\":\"No runtime PID, path, identity, or command is accepted\"}");
        return 2;
    }
    if (!normalize_signals())
        return 3;
    alarm(20);
    struct passwd *isolated = getpwnam("nobody");
    bool account_valid = isolated && isolated->pw_uid != 0 && isolated->pw_gid != 0
        && isolated->pw_uid != (uid_t)AFB_RESEARCH_UID;
    uid_t isolated_uid = isolated ? isolated->pw_uid : 0;
    gid_t isolated_gid = isolated ? isolated->pw_gid : 0;
    if (!strcmp(argv[1], "--preflight")) {
        printf("{\"effectiveUID\":%u,\"compiledUID\":%u,\"compiledGID\":%u,\"isolatedUID\":%u,\"isolatedGID\":%u,\"accountValid\":%s,\"rootStaged\":%s,\"signalsSent\":false}\n",
               geteuid(), (uid_t)AFB_RESEARCH_UID, (gid_t)AFB_RESEARCH_GID, isolated_uid, isolated_gid,
               account_valid ? "true" : "false", root_staged() ? "true" : "false");
        return 0;
    }
    bool privileged = !strcmp(argv[1], "--root-experiment");
    if (AFB_RESEARCH_UID < 500 || AFB_RESEARCH_GID == 0 || !account_valid
        || (privileged ? geteuid() != 0 || !root_staged()
                       : getuid() != (uid_t)AFB_RESEARCH_UID || geteuid() != (uid_t)AFB_RESEARCH_UID)) {
        puts("{\"status\":\"refused\",\"reason\":\"Identity or protected staging prerequisite is absent\",\"signalsSent\":false}");
        return 2;
    }
    signal(SIGPIPE, SIG_IGN);
    bool passed = trial(AFB_RESEARCH_UID, AFB_RESEARCH_GID, privileged,
                        !strcmp(argv[1], "--same-user-watchdog-control"), "same-user");
    if (privileged && passed)
        passed = trial(isolated_uid, isolated_gid, true, false, "cross-user");
    alarm(0);
    return passed ? 0 : 1;
}

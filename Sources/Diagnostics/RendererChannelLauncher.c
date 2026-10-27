#include <errno.h>
#include <fcntl.h>
#include <libproc.h>
#include <limits.h>
#include <poll.h>
#include <signal.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
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
        && info.pbi_uid == AFB_RESEARCH_UID && info.pbi_ruid == AFB_RESEARCH_UID
        && info.pbi_svuid == AFB_RESEARCH_UID && info.pbi_gid == child->identity.pbi_gid
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

static void execute(const char *application, const char *url, int socket, int output, int gate)
{
    alarm(16);
    int channel_copy = duplicate(socket), output_copy = duplicate(output), gate_copy = duplicate(gate);
    int null = open("/dev/null", O_RDONLY | O_NOFOLLOW);
    if (null < 0 || dup2(null, 0) < 0 || dup2(output_copy, 1) < 0 || dup2(output_copy, 2) < 0
        || dup2(channel_copy, 3) < 0 || dup2(gate_copy, 4) < 0) _exit(71);
    close_from(5);
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
    if (getuid() != AFB_RESEARCH_UID || geteuid() != AFB_RESEARCH_UID || argc != 3 || !valid_url(argv[2])) return 64;
    bool stalled = !strcmp(argv[1], "--stalled-control");
    bool deadline_control = !strcmp(argv[1], "--deadline-control");
    bool limit_control = !strcmp(argv[1], "--output-limit-control");
    if (!stalled && !deadline_control && !limit_control && strcmp(argv[1], "--control")) return 64;
    sigset_t mask;
    sigemptyset(&mask);
    if (sigprocmask(SIG_SETMASK, &mask, NULL)) return 65;
    int signals[] = {SIGALRM, SIGCHLD, SIGINT, SIGTERM, SIGHUP, SIGQUIT};
    for (unsigned i = 0; i < sizeof(signals)/sizeof(signals[0]); ++i)
        if (signal(signals[i], SIG_DFL) == SIG_ERR) return 65;
    signal(SIGPIPE, SIG_IGN);
    alarm(24);
    int stdout_flags = fcntl(1, F_GETFL);
    if (stdout_flags < 0 || fcntl(1, F_SETFL, stdout_flags | O_NONBLOCK)) return 65;
    char root[PATH_MAX], paths[2][PATH_MAX];
    if (snprintf(root, sizeof(root), "%s", __FILE__) >= (int)sizeof(root)) return 65;
    for (unsigned i = 0; i < 3; ++i) {
        char *end = strrchr(root, '/');
        if (!end) return 65;
        *end = 0;
    }
    const char *names[] = {"ChannelRendererProbe", "ChannelDisplayProbe"};
    for (unsigned i = 0; i < 2; ++i)
        if (snprintf(paths[i], sizeof(paths[i]), "%s/dist/%s.app/Contents/MacOS/%s", root, names[i], names[i]) >= (int)sizeof(paths[i])) return 65;
    int pair[2] = {-1,-1}, output[2] = {-1,-1}, gates[2][2] = {{-1,-1},{-1,-1}};
    int cancel[2] = {-1,-1}, armed[2] = {-1,-1};
    struct child children[2] = {{0},{0}}, guard = {0};
    bool complete = false, exceeded = false, timed_out = false, output_failed = false;
    bool cleanup = true, display_started = false, armed_guard = false;
    size_t total = 0, limit = limit_control ? 1024 : 384 * 1024;
    if (socketpair(AF_UNIX, SOCK_STREAM, 0, pair) || pipe(output) || pipe(gates[0]) || pipe(gates[1])
        || pipe(cancel) || pipe(armed)) goto finish;
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
        if (!children[i].pid) execute(paths[i], argv[2], pair[i], output[1], gates[i][0]);
        if (children[i].pid < 0 || proc_pidinfo(children[i].pid, PROC_PIDTBSDINFO, 0,
            &children[i].identity, sizeof(children[i].identity)) != sizeof(children[i].identity)
            || !same_child(&children[i])) goto finish;
        close(gates[i][0]); gates[i][0] = -1;
    }
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
    printf("CHANNEL_LAUNCHER_READY {\"rendererPID\":%d,\"displayPID\":%d,\"watchdogPID\":%d,\"ordinaryUID\":%u,\"rootRun\":false}\n",
        children[0].pid, children[1].pid, guard.pid, getuid());
    fflush(stdout);
    close(pair[0]); pair[0] = -1; close(pair[1]); pair[1] = -1;
    close(output[1]); output[1] = -1;
    if (!stalled && write(gates[0][1], "g", 1) != 1) goto finish;
    char line[65537]; size_t line_length = 0;
    double deadline = now() + (stalled ? 3 : deadline_control ? 1 : 14);
    while (now() < deadline) {
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
    int descriptors[] = {pair[0],pair[1],output[0],output[1],gates[0][0],gates[0][1],gates[1][0],gates[1][1],cancel[0],cancel[1],armed[0],armed[1]};
    for (unsigned i = 0; i < sizeof(descriptors)/sizeof(descriptors[0]); ++i) if (descriptors[i] >= 0) close(descriptors[i]);
    bool normal = true;
    for (unsigned i = 0; i < 2; ++i) normal = normal && children[i].reaped && WIFEXITED(children[i].status) && WEXITSTATUS(children[i].status) == 0;
    bool guard_normal = guard.reaped && WIFEXITED(guard.status) && WEXITSTATUS(guard.status) == 0;
    bool passed = complete && normal && guard_normal && cleanup && display_started && !exceeded && !output_failed;
    printf("\nCHANNEL_LAUNCHER_RESULT {\"passed\":%s,\"cleanupVerified\":%s,\"rendererReaped\":%s,\"displayReaped\":%s,\"watchdogReaped\":%s,\"watchdogNormalExit\":%s,\"displayStartedAfterRendererReady\":%s,\"outputLimitExceeded\":%s,\"deadlineReached\":%s,\"outputFailed\":%s,\"bytesRelayed\":%zu,\"rootRun\":false}\n",
        passed?"true":"false",cleanup?"true":"false",children[0].reaped?"true":"false",children[1].reaped?"true":"false",guard.reaped?"true":"false",guard_normal?"true":"false",display_started?"true":"false",exceeded?"true":"false",timed_out?"true":"false",output_failed?"true":"false",total);
    fflush(stdout);
    fcntl(1, F_SETFL, stdout_flags);
    alarm(0);
    return passed ? 0 : 1;
}

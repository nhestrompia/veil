#include <errno.h>
#include <libproc.h>
#include <signal.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

static double monotonic_seconds(void)
{
    struct timespec now;
    if (clock_gettime(CLOCK_MONOTONIC, &now))
        _exit(1);
    return (double)now.tv_sec + (double)now.tv_nsec / 1000000000.0;
}

static bool same_process(pid_t pid, const struct proc_bsdinfo *original, const char *path)
{
    struct proc_bsdinfo current;
    char current_path[PROC_PIDPATHINFO_MAXSIZE];
    return proc_pidinfo(pid, PROC_PIDTBSDINFO, 0, &current, sizeof(current)) == sizeof(current)
        && current.pbi_start_tvsec == original->pbi_start_tvsec
        && current.pbi_start_tvusec == original->pbi_start_tvusec
        && proc_pidpath(pid, current_path, sizeof(current_path)) > 0
        && strcmp(path, current_path) == 0;
}

int main(void)
{
    pid_t target = getpid();
    struct proc_bsdinfo original;
    char path[PROC_PIDPATHINFO_MAXSIZE];
    if (proc_pidinfo(target, PROC_PIDTBSDINFO, 0, &original, sizeof(original)) != sizeof(original)
        || proc_pidpath(target, path, sizeof(path)) <= 0)
        return 1;
    setvbuf(stdout, NULL, _IONBF, 0);
    pid_t watchdog = fork();
    if (watchdog < 0)
        return 1;
    if (watchdog == 0) {
        sleep(3);
        bool resumed = same_process(target, &original, path) && kill(target, SIGCONT) == 0;
        printf("{\"watchdogResumed\":%s}\n", resumed ? "true" : "false");
        _exit(resumed ? 0 : 1);
    }
    printf("{\"ready\":true,\"pid\":%d,\"watchdogPID\":%d}\n", target, watchdog);
    double started = monotonic_seconds();
    double previous = started;
    double maximum_gap = 0;
    while (monotonic_seconds() - started < 4) {
        struct timespec interval = { .tv_sec = 0, .tv_nsec = 20000000 };
        nanosleep(&interval, NULL);
        double now = monotonic_seconds();
        double gap = now - previous;
        if (gap > maximum_gap)
            maximum_gap = gap;
        previous = now;
    }
    int child_status;
    if (waitpid(watchdog, &child_status, 0) != watchdog
        || !WIFEXITED(child_status) || WEXITSTATUS(child_status) != 0)
        return 1;
    printf("{\"maximumGapSeconds\":%.6f,\"completed\":true}\n", maximum_gap);
    return 0;
}

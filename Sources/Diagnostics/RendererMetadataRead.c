#include <dlfcn.h>
#include <errno.h>
#include <inttypes.h>
#include <libproc.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

struct record {
    pid_t pid;
    struct proc_bsdinfo info;
    char path[PROC_PIDPATHINFO_MAXSIZE];
};

static int read_record(pid_t pid, struct record *record)
{
    record->pid = pid;
    return proc_pidinfo(pid, PROC_PIDTBSDINFO, 0, &record->info, sizeof(record->info)) == sizeof(record->info)
        && proc_pidpath(pid, record->path, sizeof(record->path)) > 0;
}

static int host_path(const char *path)
{
    char root[PATH_MAX];
    if (snprintf(root, sizeof(root), "%s", __FILE__) >= (int)sizeof(root))
        return 0;
    for (int i = 0; i < 3; ++i) {
        char *end = strrchr(root, '/');
        if (!end)
            return 0;
        *end = 0;
    }
    const char *names[] = { "RendererFilesystemReference", "RendererFilesystemSandbox", "RendererFilesystemNetworkSandbox" };
    for (size_t i = 0; i < sizeof(names) / sizeof(names[0]); ++i) {
        char expected[PATH_MAX];
        int count = snprintf(expected, sizeof(expected), "%s/dist/%s.app/Contents/MacOS/%s", root, names[i], names[i]);
        if (count > 0 && count < (int)sizeof(expected) && !strcmp(expected, path))
            return 1;
    }
    return 0;
}

static int service_path(const char *path, const char *role)
{
    const char *roots[] = { "", "/System/Volumes/Preboot/Cryptexes/OS" };
    for (size_t i = 0; i < sizeof(roots) / sizeof(roots[0]); ++i) {
        char expected[PATH_MAX];
        int count = snprintf(expected, sizeof(expected),
            "%s/System/Library/Frameworks/WebKit.framework/Versions/A/XPCServices/com.apple.WebKit.%s.xpc/Contents/MacOS/com.apple.WebKit.%s",
            roots[i], role, role);
        if (count > 0 && count < (int)sizeof(expected) && !strcmp(expected, path))
            return 1;
    }
    return 0;
}

static void json_string(const char *value)
{
    putchar('"');
    for (const unsigned char *p = (const unsigned char *)value; *p; ++p) {
        if (*p == '"' || *p == '\\')
            printf("\\%c", *p);
        else if (*p < 32)
            printf("\\u%04x", *p);
        else
            putchar(*p);
    }
    putchar('"');
}

int main(int argc, char **argv)
{
    if (getuid() == 0 || geteuid() == 0 || argc != 5)
        return 64;
    struct record records[4] = { 0 };
    const char *names[] = { "host", "content", "gpu", "network" };
    const char *roles[] = { "", "WebContent", "GPU", "Networking" };
    for (int i = 0; i < 4; ++i) {
        if (!argv[i + 1][0] || strspn(argv[i + 1], "0123456789") != strlen(argv[i + 1]))
            return 64;
        errno = 0;
        char *end = NULL;
        long pid = strtol(argv[i + 1], &end, 10);
        if (errno || *end || pid <= 1 || pid > INT_MAX || !read_record((pid_t)pid, &records[i]))
            return 65;
        if (i == 0 ? !host_path(records[i].path) : !service_path(records[i].path, roles[i]))
            return 66;
        if (records[i].info.pbi_uid != getuid() || records[i].info.pbi_ruid != getuid()
            || records[i].info.pbi_svuid != getuid())
            return 67;
        for (int j = 0; j < i; ++j) {
            if (records[j].pid == records[i].pid)
                return 68;
        }
    }
    void *library = dlopen("/usr/lib/libproc.dylib", RTLD_NOW | RTLD_LOCAL);
    pid_t (*responsible)(pid_t) = library ? dlsym(library, "responsibility_get_pid_responsible_for_pid") : NULL;
    putchar('{');
    for (int i = 0; i < 4; ++i) {
        struct proc_bsdinfo *info = &records[i].info;
        printf("%s\"%s\":{\"pid\":%d,\"path\":", i ? "," : "", names[i], records[i].pid);
        json_string(records[i].path);
        printf(",\"realUID\":%u,\"effectiveUID\":%u,\"savedUID\":%u,\"realGID\":%u,\"effectiveGID\":%u,\"savedGID\":%u,"
            "\"startedSeconds\":%" PRIu64 ",\"startedMicroseconds\":%" PRIu64 ",\"responsiblePID\":%d}",
            info->pbi_ruid, info->pbi_uid, info->pbi_svuid, info->pbi_rgid, info->pbi_gid, info->pbi_svgid,
            info->pbi_start_tvsec, info->pbi_start_tvusec, responsible ? responsible(records[i].pid) : 0);
    }
    puts("}");
    if (library)
        dlclose(library);
    return 0;
}

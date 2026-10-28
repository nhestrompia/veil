#define main renderer_signal_actor_main
#include "../Sources/Diagnostics/RendererSignalActor.c"
#undef main

int main(void)
{
    if (getuid() == 0 || geteuid() == 0) return 64;
    struct target own = {0}, foreign = {0};
    struct proc_bsdinfo reference = {0};
    bool self_read = read_target(getpid(), &own);
    bool self_reference = proc_pidinfo(getpid(), PROC_PIDTBSDINFO, 0, &reference, sizeof(reference)) == sizeof(reference);
    bool parity = self_read && self_reference
        && own.identity.pbi_uid == reference.pbi_uid && own.identity.pbi_ruid == reference.pbi_ruid
        && own.identity.pbi_svuid == reference.pbi_svuid && own.identity.pbi_gid == reference.pbi_gid
        && own.identity.pbi_rgid == reference.pbi_rgid && own.identity.pbi_svgid == reference.pbi_svgid
        && own.identity.pbi_start_tvsec == reference.pbi_start_tvsec
        && own.identity.pbi_start_tvusec == reference.pbi_start_tvusec
        && own.identity.pbi_status == reference.pbi_status;
    bool foreign_read = read_target(1, &foreign);
    bool foreign_valid = foreign_read && foreign.pid == 1 && foreign.identity.pbi_uid == 0
        && foreign.identity.pbi_ruid == 0 && foreign.identity.pbi_svuid == 0
        && foreign.identity.pbi_gid == 0 && foreign.identity.pbi_rgid == 0 && foreign.identity.pbi_svgid == 0
        && foreign.identity.pbi_start_tvsec > 0 && foreign.path[0] == '/';
    struct target invalid;
    struct metadata_failure failure;
    bool invalid_refused = !read_target_detailed(0, &invalid, &failure) && failure.error == EINVAL;
    bool gone_refused = !read_target_detailed(INT_MAX, &invalid, &failure) && failure.error == ESRCH;
    printf("{\"rootRun\":false,\"signalCalls\":0,\"ownMetadataParity\":%s,\"foreignPID1Readable\":%s,\"foreignIdentityValid\":%s,\"invalidPIDRefused\":%s,\"gonePIDRefused\":%s}\n",
        parity ? "true" : "false", foreign_read ? "true" : "false", foreign_valid ? "true" : "false",
        invalid_refused ? "true" : "false", gone_refused ? "true" : "false");
    return parity && foreign_valid && invalid_refused && gone_refused ? 0 : 1;
}

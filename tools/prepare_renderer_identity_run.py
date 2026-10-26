"""Prepare a literal, hash-bound renderer test without requesting elevation."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import stat
import subprocess


ROOT = Path(__file__).resolve().parents[1]
SUPERVISOR = ROOT / ".build/renderer-identity-supervisor"
APP = ROOT / "dist/RendererIdentityProbe.app"
APP_FILES = ("Contents/Info.plist", "Contents/MacOS/RendererIdentityProbe", "Contents/_CodeSignature/CodeResources")


def perl_string(value):
    return "'" + str(value).replace("\\", "\\\\").replace("'", "\\'") + "'"


def copy_program(manifest, source_uid, stage_uid=0):
    rows = ",\n".join("[" + ",".join((perl_string(item["source"]), perl_string(item["staged"]), str(item["size"]))) + "]"
                       for item in manifest)
    return f'''use strict;
use warnings;
use Fcntl qw(:DEFAULT :mode);
use POSIX qw(SIG_SETMASK sigprocmask);
use Errno qw(EINTR);
sigprocmask(SIG_SETMASK, POSIX::SigSet->new()) or die "signal mask";
$SIG{{ALRM}} = 'DEFAULT';
alarm(10);
umask(077);
@ARGV == 1 or die "stage argument";
my ($stage) = $ARGV[0] =~ m{{\\A(/private/tmp/agentfreebrowser-renderer\\.[A-Za-z0-9]{{6}})\\z}};
defined($stage) or die "stage path";
my @directory = lstat($stage);
S_ISDIR($directory[2]) && $directory[4] == {stage_uid} && ($directory[2] & 07777) == 0700 or die "stage metadata";
my @files = ({rows});
for my $item (@files) {{
    my ($source, $relative, $size) = @$item;
    sysopen(my $input, $source, O_RDONLY | O_NOFOLLOW | O_NONBLOCK) or die "source open";
    my @info = stat($input);
    S_ISREG($info[2]) && $info[4] == {source_uid} && $info[3] == 1
        && ($info[2] & 0022) == 0 && $info[7] == $size or die "source metadata";
    sysopen(my $output, "$stage/$relative", O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW, 0600) or die "destination open";
    binmode($input); binmode($output);
    my $total = 0;
    while ($total < $size) {{
        my $length = $size - $total > 65536 ? 65536 : $size - $total;
        my $buffer;
        my $count = sysread($input, $buffer, $length);
        if (!defined($count)) {{ next if $! == EINTR; die "source read"; }}
        $count > 0 or die "source shortened";
        my $offset = 0;
        while ($offset < $count) {{
            my $written = syswrite($output, $buffer, $count - $offset, $offset);
            if (!defined($written)) {{ next if $! == EINTR; die "destination write"; }}
            $written > 0 or die "destination stalled";
            $offset += $written;
        }}
        $total += $count;
    }}
    my $extra;
    my $end = sysread($input, $extra, 1);
    defined($end) && $end == 0 or die "source length changed";
    close($input) or die "source close";
    close($output) or die "destination close";
}}
alarm(0);
'''


def bounded_tool(command, arguments):
    # Only this generator supplies the command and fixed relative argument list.
    values = [perl_string(command)] + [
        '"$stage/' + value[6:] + '"' if value.startswith("STAGE/") else perl_string(value)
        for value in arguments]
    code = r'''use strict; use warnings; use POSIX qw(SIG_SETMASK sigprocmask);
sigprocmask(SIG_SETMASK, POSIX::SigSet->new()) or die "signal mask";
$SIG{ALRM} = 'DEFAULT'; alarm(8);
$ENV{PATH} = '/usr/bin:/bin:/usr/sbin:/sbin';
delete @ENV{qw(IFS CDPATH ENV BASH_ENV PERL5LIB PERL5OPT)};
my ($stage) = $ARGV[0] =~ m{\A(/private/tmp/agentfreebrowser-renderer\.[A-Za-z0-9]{6})\z};
defined($stage) or die "stage path";
exec(''' + ",".join(values) + ''') or die "fixed tool exec";'''
    return "/usr/bin/perl -T -e " + shlex.quote(code) + ' "$stage"'


def stage_script(manifest, source_uid, libraries, stage_uid=0, observe_signals=False):
    fixed_files = [item["staged"] for item in manifest]
    if observe_signals:
        fixed_files.append("observation.log")
    dirs = ["RendererIdentityProbe.app", "RendererIdentityProbe.app/Contents",
            "RendererIdentityProbe.app/Contents/MacOS", "RendererIdentityProbe.app/Contents/_CodeSignature"]
    quoted_files = " ".join('"$stage/' + value + '"' for value in fixed_files)
    quoted_dirs = " ".join('"$stage/' + value + '"' for value in dirs)
    cleanup_dirs = " ".join('"$stage/' + value + '"' for value in reversed(dirs))
    copy = "/usr/bin/perl -T -e " + shlex.quote(copy_program(manifest, source_uid, stage_uid)) + ' "$stage"'
    hashes = "\n".join(
        'actual=$(/usr/bin/shasum -a 256 "$stage/' + item["staged"] + '")\n'
        'test "$actual" = "' + item["sha256"] + '  $stage/' + item["staged"] + '"'
        for item in manifest)
    checks = []
    for relative in ("renderer-identity-supervisor", "RendererIdentityProbe.app"):
        checks.append(bounded_tool("/usr/bin/codesign", ["--verify", "--strict", "STAGE/" + relative]))
        show = bounded_tool("/usr/bin/codesign", ["-d", "--verbose=2", "STAGE/" + relative])
        checks.append('signature=$(' + show + ' 2>&1)\ncase "$signature" in *\'runtime)\'*) ;; *) exit 2 ;; esac')
    for relative, expected in libraries.items():
        tool = bounded_tool("/usr/bin/otool", ["-L", "STAGE/" + relative])
        checks.append('library_output=$(' + tool + ')\n'
                      'dependencies=$(printf \'%s\\n\' "$library_output" | /usr/bin/awk \'NR>1 {print $1}\')\n'
                      'test "$dependencies" = ' + shlex.quote("\n".join(expected)))
        tool = bounded_tool("/usr/bin/otool", ["-l", "STAGE/" + relative])
        checks.append('commands=$(' + tool + ')\ncase "$commands" in *LC_RPATH*|*LC_DYLD_ENVIRONMENT*) exit 2 ;; esac')
    observer_setup = '''set -C
exec 3> "$stage/observation.log"
set +C
/bin/chmod 0444 "$stage/observation.log"
''' if observe_signals else ""
    observer_redirect = ' >&3 2>&1' if observe_signals else ""
    observer_replay = 'exec 3>&-\n/bin/cat "$stage/observation.log"\n' if observe_signals else ""
    return '''set -eu
umask 077
stage=$(/usr/bin/mktemp -d /private/tmp/agentfreebrowser-renderer.XXXXXX)
cleanup() {
    cleanup_status=0
    for directory in "$stage" ''' + quoted_dirs + '''; do
        if [ -d "$directory" ]; then /bin/chmod 0700 "$directory" || cleanup_status=1; fi
    done
    /bin/rm -f -- ''' + quoted_files + ''' || cleanup_status=1
    cd /private/tmp || return 1
    for directory in ''' + cleanup_dirs + ''' "$stage"; do
        if [ -d "$directory" ]; then /bin/rmdir -- "$directory" || cleanup_status=1; fi
    done
    return "$cleanup_status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
/bin/chmod -N "$stage"
/bin/chmod 0700 "$stage"
/bin/mkdir -p -- ''' + quoted_dirs + '''
cd "$stage"
''' + copy + "\n" + hashes + '''
/bin/chmod 0700 "$stage/renderer-identity-supervisor" "$stage/RendererIdentityProbe.app/Contents/MacOS/RendererIdentityProbe"
''' + "\n".join(checks) + ("\n" + observer_setup if observe_signals else "") + '''
/bin/chmod -N ''' + quoted_files + " " + quoted_dirs + '''
/bin/chmod 0444 ''' + quoted_files + '''
/bin/chmod 0700 "$stage/renderer-identity-supervisor"
/bin/chmod 0555 "$stage/RendererIdentityProbe.app/Contents/MacOS/RendererIdentityProbe" ''' + quoted_dirs + '''
/bin/chmod 0711 "$stage"
set +e
/usr/bin/env -i PATH=/usr/bin:/bin:/usr/sbin:/sbin LC_ALL=C "$stage/renderer-identity-supervisor" --root-smoke''' + observer_redirect + '''
helper_status=$?
set -e
''' + observer_replay + '''cleanup
trap - EXIT
test ! -e "$stage"
printf '\\nSTAGING_RESULT {"helperExitCode":%s,"temporaryDirectory":"%s","stagingRemoved":true}\\n' "$helper_status" "$stage"
'''


def prepare(output):
    if os.getuid() == 0 or os.geteuid() == 0:
        raise ValueError("Prepare only as the ordinary research user")
    actual = sorted(str(path.relative_to(APP)) for path in APP.rglob("*") if path.is_file())
    if actual != sorted(APP_FILES):
        raise ValueError("The probe bundle must contain exactly three known files")
    manifest = []
    for source, staged in [(SUPERVISOR, "renderer-identity-supervisor"), *[(APP / name, "RendererIdentityProbe.app/" + name) for name in APP_FILES]]:
        info = source.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1 or info.st_mode & 0o022:
            raise ValueError("A source image has unsafe metadata")
        if source.resolve() != source or not 0 < info.st_size <= 8 * 1024 * 1024:
            raise ValueError("A source image has an unexpected path or size")
        manifest.append({"source": str(source), "staged": staged, "size": info.st_size,
                         "sha256": hashlib.sha256(source.read_bytes()).hexdigest()})
    libraries = {}
    for binary in (SUPERVISOR, APP / "Contents/MacOS/RendererIdentityProbe"):
        subprocess.run(["codesign", "--verify", "--strict", str(binary)], check=True, capture_output=True)
        show = subprocess.run(["codesign", "-dvv", str(binary)], check=True, capture_output=True, text=True)
        if "runtime)" not in show.stderr:
            raise ValueError("Both executables require hardened runtime")
        deps = subprocess.run(["otool", "-L", str(binary)], check=True, capture_output=True, text=True).stdout
        dependencies = [line.strip().split()[0] for line in deps.splitlines()[1:]]
        if any(not value.startswith(("/usr/lib/", "/System/Library/Frameworks/")) for value in dependencies):
            raise ValueError("Only absolute system dependencies are accepted")
        if binary == SUPERVISOR and dependencies != ["/usr/lib/libSystem.B.dylib"]:
            raise ValueError("The root supervisor must load only libSystem")
        load = subprocess.run(["otool", "-l", str(binary)], check=True, capture_output=True, text=True).stdout
        if "LC_RPATH" in load or "LC_DYLD_ENVIRONMENT" in load:
            raise ValueError("Loader overrides are forbidden")
        key = "renderer-identity-supervisor" if binary == SUPERVISOR else "RendererIdentityProbe.app/Contents/MacOS/RendererIdentityProbe"
        libraries[key] = dependencies
    preflight = json.loads(subprocess.run([str(SUPERVISOR), "--preflight"], check=True, capture_output=True, text=True, timeout=4).stdout)
    script = stage_script(manifest, os.getuid(), libraries)
    command = "/usr/bin/env -i PATH=/usr/bin:/bin:/usr/sbin:/sbin LC_ALL=C /bin/sh -c " + shlex.quote(script)
    result = {"manifest": manifest, "libraries": libraries, "preflight": preflight,
              "administratorCommand": command, "administratorCommandSHA256": hashlib.sha256(command.encode()).hexdigest(),
              "rootRun": False, "elevationRequested": False, "approvedRunCount": 0,
              "supervisorDeadlineSeconds": 32, "childOutputLimitBytes": 3 * 1024 * 1024,
              "wholeCommandDeadlineSeconds": None,
              "scope": "One proposed fixed inline cross-user renderer smoke test. No signal attack or service/account/grant change.",
              "uncertainties": ["OS-managed per-user caches outside staging", "shared nobody state", "inherited GUI/security capabilities", "auxiliary lifecycle and sampled identity coverage",
                                "The 32-second deadline covers only the supervisor phase",
                                "SIGKILL of the outer staging shell can leave its fixed staging files"]}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = prepare(args.output)
    print(json.dumps({"administratorCommandSHA256": result["administratorCommandSHA256"], "rootRun": False}))

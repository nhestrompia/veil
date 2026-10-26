"""Prepare a hash-bound, finite administrator test. This tool never elevates."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import stat
import subprocess

from run_native import ROOT


def stage_script(binary, digest):
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise ValueError("A literal SHA256 is required")
    source = shlex.quote(str(binary))
    return f'''set -eu
umask 077
stage=$(/usr/bin/mktemp -d /private/tmp/agentfreebrowser-identity.XXXXXX)
cleanup() {{
    /bin/rm -f -- "$stage/identity-signal-control"
    cd /private/tmp
    /bin/rmdir -- "$stage"
}}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
/bin/chmod -N "$stage"
/bin/chmod 0700 "$stage"
/bin/cp -X -- {source} "$stage/identity-signal-control"
/bin/chmod -N "$stage/identity-signal-control"
/bin/chmod 0700 "$stage/identity-signal-control"
actual=$(/usr/bin/shasum -a 256 "$stage/identity-signal-control")
expected="{digest}  $stage/identity-signal-control"
if [ "$actual" != "$expected" ]; then
    echo 'The staged helper hash differs. No experiment ran.' >&2
    exit 2
fi
/usr/bin/codesign --verify --strict "$stage/identity-signal-control"
signature=$(/usr/bin/codesign -d --verbose=2 "$stage/identity-signal-control" 2>&1)
case "$signature" in
    *'runtime)'*) ;;
    *) echo 'The staged helper lacks Hardened Runtime.' >&2; exit 2 ;;
esac
dependencies=$(/usr/bin/otool -L "$stage/identity-signal-control" | /usr/bin/awk 'NR>1 {{print $1}}')
if [ "$dependencies" != /usr/lib/libSystem.B.dylib ]; then
    echo 'The staged helper has an unexpected dependency.' >&2
    exit 2
fi
load_commands=$(/usr/bin/otool -l "$stage/identity-signal-control")
case "$load_commands" in
    *LC_RPATH*|*LC_DYLD_ENVIRONMENT*) echo 'The staged helper adds loader configuration.' >&2; exit 2 ;;
esac
cd "$stage"
set +e
/usr/bin/env -i PATH=/usr/bin:/bin:/usr/sbin:/sbin LC_ALL=C "$stage/identity-signal-control" --root-experiment
helper_status=$?
set -e
cleanup
trap - EXIT
test ! -e "$stage"
printf '{{"status":"root-run-finished","helperExitCode":%s,"temporaryDirectory":"%s","temporaryCleanupVerified":true}}\\n' "$helper_status" "$stage"
'''


def prepare(output):
    binary = ROOT / ".build/identity-signal-control"
    metadata = binary.lstat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != os.getuid() or metadata.st_nlink != 1 or metadata.st_mode & 0o022:
        raise ValueError("The native helper must be a regular file without shared write access")
    subprocess.run(["/usr/bin/codesign", "--verify", "--strict", str(binary)], check=True, capture_output=True)
    signature = subprocess.run(["/usr/bin/codesign", "-d", "--verbose=2", str(binary)], check=True, capture_output=True, text=True)
    if "runtime)" not in signature.stderr:
        raise ValueError("The helper must retain Hardened Runtime")
    libraries = subprocess.run(["/usr/bin/otool", "-L", str(binary)], check=True, capture_output=True, text=True).stdout
    dependencies = [line.strip().split(" ", 1)[0] for line in libraries.splitlines()[1:]]
    if dependencies != ["/usr/lib/libSystem.B.dylib"]:
        raise ValueError("The helper may load only the native system library")
    commands = subprocess.run(["/usr/bin/otool", "-l", str(binary)], check=True, capture_output=True, text=True).stdout
    if "LC_DYLD_ENVIRONMENT" in commands or "LC_RPATH" in commands:
        raise ValueError("The helper must not add loader environments or run paths")
    preflight = json.loads(subprocess.run([str(binary), "--preflight"], check=True, capture_output=True, text=True).stdout)
    if preflight["effectiveUID"] != preflight["compiledUID"] or preflight["effectiveUID"] < 500 or not preflight["accountValid"]:
        raise ValueError("Prepare the experiment as its compiled ordinary user")
    digest = hashlib.sha256(binary.read_bytes()).hexdigest()
    script = stage_script(binary, digest)
    # The administrator shell also starts with a clean environment before it loads code.
    command = "/usr/bin/env -i PATH=/usr/bin:/bin:/usr/sbin:/sbin LC_ALL=C /bin/sh -c " + shlex.quote(script)
    plan = {"binary": str(binary), "binarySHA256": digest, "preflight": preflight,
            "dependencies": dependencies, "administratorCommand": command,
            "administratorCommandSHA256": hashlib.sha256(command.encode()).hexdigest(),
            "elevationRequested": False, "rootExperimentRun": False,
            "scope": "Finite own-child signal tests, twenty-second parent deadline. No account, service, browser, or permission changes."}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(plan, indent=2) + "\n")
    return plan


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    plan = prepare(args.output)
    print(json.dumps({key: plan[key] for key in ["binarySHA256", "administratorCommandSHA256", "elevationRequested", "rootExperimentRun"]}))

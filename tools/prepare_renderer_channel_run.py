"""Prepare one literal cross-user channel comparison without elevation."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import shlex
import stat
import subprocess
from urllib.parse import urlsplit

from prepare_renderer_identity_run import ROOT, bounded_tool, copy_program
from run_renderer_channel_preflight import SUPERVISOR, RENDERER_ACTOR, DISPLAY_ACTOR

APP_NAMES = ('ChannelIsolatedRendererProbe', 'ChannelIsolatedDisplayProbe')
HELPER = 'renderer-channel-supervisor'
DIRECTORIES = tuple(name + '.app' + suffix for name in APP_NAMES
                    for suffix in ('', '/Contents', '/Contents/MacOS', '/Contents/_CodeSignature'))
FIXED_FILES = (HELPER, *[name + '.app/Contents/' + suffix for name in APP_NAMES
                        for suffix in ('Info.plist', 'MacOS/' + name, '_CodeSignature/CodeResources')])


def validate_url(url):
    if type(url) is not str:
        raise ValueError('Expected a fixed fixture URL')
    value = urlsplit(url)
    if (value.scheme != 'http' or value.hostname != '127.0.0.1' or value.username or value.password
            or value.port is None or not 1024 <= value.port <= 65535 or value.query or value.fragment
            or not value.path.startswith('/channel/')):
        raise ValueError('Unexpected fixture URL')
    nonce = value.path.removeprefix('/channel/')
    if len(nonce) != 16 or any(char not in '0123456789abcdef' for char in nonce):
        raise ValueError('Unexpected fixture nonce')
    if url != f'http://127.0.0.1:{value.port}/channel/{nonce}':
        raise ValueError('Use the canonical fixed fixture URL')
    return value.port, nonce


def stage_script(manifest, source_uid, libraries, url, stage_uid=0):
    validate_url(url)
    if sorted(item['staged'] for item in manifest) != sorted(FIXED_FILES):
        raise ValueError('Expected exactly the fixed supervisor and two three-file bundles')
    if set(libraries) != {HELPER, *[name + '.app/Contents/MacOS/' + name for name in APP_NAMES]}:
        raise ValueError('Unexpected dependency profile')
    quote = lambda relative: '"$stage/' + relative + '"'
    files = ' '.join(quote(value) for value in (*FIXED_FILES, 'observation.log'))
    directories = ' '.join(quote(value) for value in DIRECTORIES)
    reverse_dirs = ' '.join(quote(value) for value in reversed(DIRECTORIES))
    executables = ' '.join(quote(name + '.app/Contents/MacOS/' + name) for name in APP_NAMES)
    copy = '/usr/bin/perl -T -e ' + shlex.quote(copy_program(manifest, source_uid, stage_uid)) + ' "$stage"'
    hashes = '\n'.join('actual=$(/usr/bin/shasum -a 256 ' + quote(item['staged']) + ')\n'
                      'test "$actual" = "' + item['sha256'] + '  $stage/' + item['staged'] + '"' for item in manifest)
    checks = []
    for relative in (HELPER, *[name + '.app' for name in APP_NAMES]):
        checks.append(bounded_tool('/usr/bin/codesign', ['--verify', '--strict', 'STAGE/' + relative]))
        checks.append('signature=$(' + bounded_tool('/usr/bin/codesign', ['-d', '--verbose=2', 'STAGE/' + relative])
                      + ' 2>&1)\ncase "$signature" in *\'runtime)\'*) ;; *) exit 2 ;; esac')
    for relative, dependencies in libraries.items():
        checks.append('library_output=$(' + bounded_tool('/usr/bin/otool', ['-L', 'STAGE/' + relative]) + ')\n'
                      'dependencies=$(printf \'%s\\n\' "$library_output" | /usr/bin/awk \'NR>1 {print $1}\')\n'
                      'test "$dependencies" = ' + shlex.quote('\n'.join(dependencies)))
        checks.append('commands=$(' + bounded_tool('/usr/bin/otool', ['-l', 'STAGE/' + relative]) + ')\n'
                      'case "$commands" in *LC_RPATH*|*LC_DYLD_ENVIRONMENT*) exit 2 ;; esac')
    return '''set -eu
umask 077
stage=$(/usr/bin/mktemp -d /private/tmp/agentfreebrowser-renderer.XXXXXX)
cleanup() {
    cleanup_status=0
    for directory in "$stage" ''' + directories + '''; do
        if [ -d "$directory" ]; then /bin/chmod 0700 "$directory" || cleanup_status=1; fi
    done
    /bin/rm -f -- ''' + files + ''' || cleanup_status=1
    cd /private/tmp || return 1
    for directory in ''' + reverse_dirs + ''' "$stage"; do
        if [ -d "$directory" ]; then /bin/rmdir -- "$directory" || cleanup_status=1; fi
    done
    return "$cleanup_status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
/bin/chmod -N "$stage"
/bin/chmod 0700 "$stage"
/bin/mkdir -p -- ''' + directories + '''
cd "$stage"
''' + copy + '\n' + hashes + '''
/bin/chmod 0700 "$stage/renderer-channel-supervisor" ''' + executables + '\n' + '\n'.join(checks) + '''
set -C
exec 3> "$stage/observation.log"
set +C
/bin/chmod -N ''' + files + ' ' + directories + '''
/bin/chmod 0444 ''' + files + '''
/bin/chmod 0700 "$stage/renderer-channel-supervisor"
/bin/chmod 0555 ''' + executables + ' ' + directories + '''
/bin/chmod 0711 "$stage"
set +e
/usr/bin/env -i PATH=/usr/bin:/bin:/usr/sbin:/sbin LC_ALL=C "$stage/renderer-channel-supervisor" --root-channel ''' + shlex.quote(url) + ''' >&3 2>&1
helper_status=$?
set -e
exec 3>&-
/bin/cat "$stage/observation.log"
cleanup
trap - EXIT
test ! -e "$stage"
printf '\\nSTAGING_RESULT {"helperExitCode":%s,"temporaryDirectory":"%s","stagingRemoved":true}\\n' "$helper_status" "$stage"
'''


def prepare(output):
    if os.getuid() != 501 or os.geteuid() != os.getuid(): raise ValueError('Prepare as the ordinary research user')
    manifest = []
    sources = [(SUPERVISOR, HELPER)]
    for name in APP_NAMES:
        app = ROOT / ('dist/' + name + '.app')
        expected = ['Contents/Info.plist', 'Contents/MacOS/' + name, 'Contents/_CodeSignature/CodeResources']
        if sorted(str(path.relative_to(app)) for path in app.rglob('*') if path.is_file()) != sorted(expected):
            raise ValueError('Unexpected app bundle contents')
        sources.extend((app / relative, app.name + '/' + relative) for relative in expected)
    for source, staged in sources:
        info = source.lstat()
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1
                or info.st_mode & 0o022 or source.resolve() != source or not 0 < info.st_size <= 8 * 1024 * 1024):
            raise ValueError('Unsafe source metadata')
        manifest.append({'source': str(source), 'staged': staged, 'size': info.st_size,
                         'sha256': hashlib.sha256(source.read_bytes()).hexdigest()})
    libraries = {}
    for binary, relative in [(SUPERVISOR, HELPER), *[(ROOT / 'dist' / (name + '.app/Contents/MacOS/' + name),
            name + '.app/Contents/MacOS/' + name) for name in APP_NAMES]]:
        subprocess.run(['codesign', '--verify', '--strict', str(binary)], check=True, capture_output=True)
        signature = subprocess.run(['codesign', '-dvv', str(binary)], check=True, capture_output=True, text=True)
        if 'runtime)' not in signature.stderr: raise ValueError('Hardened runtime is required')
        deps = subprocess.run(['otool', '-L', str(binary)], check=True, capture_output=True, text=True).stdout
        dependencies = [line.strip().split()[0] for line in deps.splitlines()[1:]]
        if any(not item.startswith(('/usr/lib/', '/System/Library/Frameworks/')) for item in dependencies):
            raise ValueError('Only absolute system dependencies are accepted')
        if binary == SUPERVISOR and dependencies != ['/usr/lib/libSystem.B.dylib']:
            raise ValueError('The supervisor must load only libSystem')
        load = subprocess.run(['otool', '-l', str(binary)], check=True, capture_output=True, text=True).stdout
        if 'LC_RPATH' in load or 'LC_DYLD_ENVIRONMENT' in load: raise ValueError('Loader overrides refuse')
        libraries[relative] = dependencies
    url = 'http://127.0.0.1:8767/channel/' + secrets.token_hex(8)
    script = stage_script(manifest, os.getuid(), libraries, url)
    command = '/usr/bin/env -i PATH=/usr/bin:/bin:/usr/sbin:/sbin LC_ALL=C /bin/sh -c ' + shlex.quote(script)
    source_names = ['Sources/Diagnostics/RendererChannelLauncher.c', 'Sources/Diagnostics/RendererSignalActor.c',
        'Sources/Channel/RendererChannel.swift', 'Sources/Diagnostics/ChannelProbeSupport.swift',
        'Sources/Diagnostics/ChannelRendererProbe.swift', 'Sources/Diagnostics/ChannelDisplayProbe.swift',
        'Sources/Browser/BrowserRuntimePolicy.swift', 'scripts/build-renderer-channel-supervisor.sh',
        'tools/prepare_renderer_channel_run.py', 'tools/run_renderer_channel_preflight.py',
        'tools/run_renderer_channel_control.py', 'tools/observe_renderer_channel.py',
        'tools/prepare_renderer_identity_run.py', 'tools/observe_renderer_signals.py',
        'tools/run_renderer_channel_launcher.py', 'tools/run_renderer_signal_reference.py', 'tools/process_cleanup.py']
    result = {'manifest': manifest, 'libraries': libraries, 'fixtureURL': url,
        'administratorCommand': command, 'administratorCommandSHA256': hashlib.sha256(command.encode()).hexdigest(),
        'maximumRuns': 1, 'repeatOnFailure': False, 'rootRun': False, 'elevationRequested': False,
        'ordinaryUID': os.getuid(), 'ordinaryGID': os.getgid(), 'isolatedUID': 4294967294, 'isolatedGID': 4294967294,
        'actorSHA256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (RENDERER_ACTOR, DISPLAY_ACTOR)},
        'sourceSHA256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in source_names},
        'supervisorAlarmSeconds': 24, 'childAlarmSeconds': 16, 'watchdogAlarmSeconds': 20,
        'outputLimitBytes': 384 * 1024, 'wholeCommandDeadlineSeconds': None,
        'scope': 'One fixed local cross-user channel comparison. Root only stages verified bytes, creates two known app children, permanently drops them to nobody and the ordinary identity, relays bounded diagnostic output, and cleans its own children and fixed files.',
        'limits': ['Inherited GUI and audit capabilities, shared nobody state, and OS-managed caches remain unconfined.',
            'The native alarms do not bound authentication or the whole staging command.',
            'SIGKILL of the outer staging shell can leave its fixed staging files.',
            'Auxiliary WebKit cleanup after interrupted runs remains incomplete.',
            'Fault controls begin after watchdog acknowledgement. Earlier startup interruption is not fully measured.',
            'No physical input, visible display, capture, or general website acceptance claim.']}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=Path)
    result = prepare(parser.parse_args().output)
    print(json.dumps({'administratorCommandSHA256': result['administratorCommandSHA256'], 'rootRun': False}))

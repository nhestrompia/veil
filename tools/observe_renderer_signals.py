"""Read a fixed staged research report and run only the ordinary-user actor."""

import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import time

from run_renderer_signal_reference import ACTOR, actor_arguments, prefixed

STAGE_PATTERN = re.compile(r'/private/tmp/agentfreebrowser-renderer\.[A-Za-z0-9]{6}\Z')
LIMIT = 3 * 1024 * 1024 + 16384


def private_stages():
    return {str(path) for path in Path('/private/tmp').glob('agentfreebrowser-renderer.??????')
            if STAGE_PATTERN.fullmatch(str(path))}


def read_fixed_file(path, owner, mode, maximum):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(descriptor)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != owner or info.st_nlink != 1
                or stat.S_IMODE(info.st_mode) != mode or info.st_size > maximum):
            raise ValueError('Unexpected staged file metadata')
        data = bytearray()
        while len(data) <= maximum:
            block = os.read(descriptor, min(65536, maximum + 1 - len(data)))
            if not block:
                return bytes(data)
            data.extend(block)
        raise ValueError('The staged file exceeds the byte limit')
    finally:
        os.close(descriptor)


def read_native(stage, plan, owner=0):
    stage = Path(stage)
    if not STAGE_PATTERN.fullmatch(str(stage)):
        raise ValueError('Unexpected staging path')
    info = stage.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != owner:
        raise ValueError('Unexpected staging directory metadata')
    if stat.S_IMODE(info.st_mode) == 0o700:
        return None
    if stat.S_IMODE(info.st_mode) != 0o711:
        raise ValueError('Unexpected staging directory metadata')
    data = read_fixed_file(stage / 'observation.log', owner, 0o444, LIMIT)
    complete = data.rsplit(b'\n', 1)[0] if b'\n' in data else b''
    values = prefixed(complete + b'\n', 'HEADLESS_RENDERER_RESULT ')
    if not values:
        return None
    if len(values) != 1:
        raise ValueError('Duplicate native report')
    for item in plan['manifest']:
        mode = 0o700 if item['staged'] == 'renderer-identity-supervisor' else (
            0o555 if '/MacOS/' in item['staged'] else 0o444)
        if item['staged'] == 'renderer-identity-supervisor':
            metadata = (stage / item['staged']).lstat()
            if (not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != owner or metadata.st_nlink != 1
                    or stat.S_IMODE(metadata.st_mode) != mode or metadata.st_size != item['size']):
                raise ValueError('Unexpected staged supervisor metadata')
            # The root staging command checks these bytes. The observer cannot read mode0700.
            continue
        image = read_fixed_file(stage / item['staged'], owner, mode, item['size'])
        if len(image) != item['size'] or hashlib.sha256(image).hexdigest() != item['sha256']:
            raise ValueError('The staged image differs from the reviewed manifest')
    native = values[0]
    if not isinstance(native, dict) or not all(native.get(key) is True for key in
            ('completed', 'identityControl', 'javascriptPassed', 'snapshotPassed', 'serviceIdentityStable')):
        raise ValueError('The native rendering control failed')
    expected_path = str(stage / 'RendererIdentityProbe.app/Contents/MacOS/RendererIdentityProbe')
    if native.get('host', {}).get('path') != expected_path:
        raise ValueError('The native report names another host')
    native.pop('snapshotPNGBase64', None)
    return native


def observe(plan, baseline, output, launch_process):
    if os.getuid() == 0 or os.geteuid() == 0:
        raise ValueError('The signal observer must never run as root')
    if hashlib.sha256(ACTOR.read_bytes()).hexdigest() != plan['actorSHA256']:
        raise ValueError('The actor differs from the reviewed image')
    result = {'actorUID': os.getuid(), 'attempted': False,
              'supervisorHashScope': 'root-staging-verification-only',
              'appHashScope': 'ordinary-user-observer'}
    while launch_process.poll() is None:
        candidates = private_stages() - baseline
        if len(candidates) > 1:
            result['error'] = 'Multiple new research stages appeared. No signal attempt.'
            break
        if candidates:
            try:
                stage = next(iter(candidates))
                native = read_native(stage, plan)
                if native is not None:
                    result.update({'attempted': True, 'stage': stage, 'native': native})
                    actor = subprocess.run(actor_arguments(native, isolated=True), capture_output=True, timeout=9)
                    (output / 'actor.stdout').write_bytes(actor.stdout)
                    (output / 'actor.stderr').write_bytes(actor.stderr)
                    rows = prefixed(actor.stdout, 'SIGNAL_RESULT ')
                    footer = prefixed(actor.stdout, 'SIGNAL_ACTOR_RESULT ')
                    result.update({'exitCode': actor.returncode, 'signals': rows, 'footer': footer,
                                       'allPauseAttemptsDenied': actor.returncode == 0 and len(rows) == 4
                                       and all(row.get('expectedOutcome') is True for row in rows)
                                       and len(footer) == 1 and footer[0].get('passed') is True})
                    break
            except FileNotFoundError:
                pass
            except (ValueError, OSError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
                result['error'] = str(error)
                break
        time.sleep(0.01)
    (output / 'observer.json').write_text(json.dumps(result, indent=2) + '\n')
    return result

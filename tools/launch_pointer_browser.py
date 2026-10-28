"""Launch only the pinned hardware-pointer candidate with existing permissions."""

import argparse
import json
from pathlib import Path
import subprocess

from build_focus_browser import digest, MANIFEST as ENGINE_MANIFEST
from build_pointer_browser import APP, MANIFEST, NAME
from launch_focus_browser import verified_target as verified_engine
from process_cleanup import matching_pids, stop_launched


def verified_target():
    record = json.loads(MANIFEST.read_text())
    target = record['targets'][NAME]
    binary = APP / 'Contents/MacOS' / NAME
    if target['path'] != str(APP) or digest(binary) != target['binarySHA256']:
        raise RuntimeError('The pinned hardware-pointer candidate changed')
    _, environment = verified_engine()
    engine = json.loads(ENGINE_MANIFEST.read_text())
    if record['engineRoot'] != engine['engineRoot'] or record['engineSHA256'] != engine['engineSHA256']:
        raise RuntimeError('The hardware-pointer engine pins differ from the tested engine')
    subprocess.run(['codesign', '--verify', '--strict', str(APP)], check=True, capture_output=True, timeout=10)
    return binary, environment


def launch(log, arguments):
    binary, environment = verified_target()
    if matching_pids(binary):
        raise RuntimeError('The hardware-pointer candidate already runs')
    environment = {key: value for key, value in environment.items()
                   if not key.startswith(('DYLD_', '__XPC_DYLD_', 'AFB_'))}
    log = log.resolve()
    log.write_text('')
    process = subprocess.Popen(['open', '-n', '-W', str(APP), '--stdout', str(log), '--stderr', str(log),
                                '--args', *arguments], env=environment,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    process.research_existing_pids = set()
    return process, binary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request-permissions', action='store_true')
    parser.add_argument('--log', type=Path, required=True)
    args = parser.parse_args()
    if args.request_permissions and not json.loads(MANIFEST.read_text()).get('permissionApproved'):
        raise RuntimeError('This exact candidate needs approval before its permission request')
    process, binary = launch(args.log, ['--request-permissions' if args.request_permissions else '--permissions'])
    try:
        process.wait(timeout=20)
    finally:
        if not stop_launched(process, binary):
            raise RuntimeError('The candidate permission preflight did not stop')
    print(args.log.read_text())

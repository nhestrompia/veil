"""Launch only the hash-pinned focus browser with its workspace research engine."""

import argparse
import json
from pathlib import Path
import subprocess

from build_focus_browser import MANIFEST, TARGETS, digest
from engine_runtime import BASE, engine_environment
from process_cleanup import matching_pids
from process_cleanup import stop_launched
from run_native import ROOT


def verified_target(name='AgentFreeBrowserEngine'):
    if name not in TARGETS:
        raise ValueError('Unknown focus-browser target')
    manifest = json.loads(MANIFEST.read_text())
    target = manifest['targets'][name]
    app = ROOT / TARGETS[name][0] / (name + '.app')
    binary = app / 'Contents/MacOS' / name
    if target['path'] != str(app) or digest(binary) != target['binarySHA256']:
        raise RuntimeError('The pinned focus browser changed')
    root = (BASE / 'output/Release').resolve()
    if manifest['engineRoot'] != str(root):
        raise RuntimeError('The engine root changed')
    for relative, expected in manifest['engineSHA256'].items():
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or digest(path) != expected:
            raise RuntimeError('A pinned engine image changed')
    subprocess.run(['codesign', '--verify', '--strict', str(app)], check=True, capture_output=True, timeout=10)
    return binary, engine_environment(root)


def launch(log, arguments, name='AgentFreeBrowserEngine'):
    binary, environment = verified_target(name)
    if matching_pids(binary):
        raise RuntimeError('This focus-browser target already runs')
    with log.open('w') as stream:
        process = subprocess.Popen([str(binary), *arguments], env=environment,
                                   stdout=stream, stderr=subprocess.STDOUT)
    process.research_existing_pids = set()
    return process, binary


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--permissions', action='store_true')
    parser.add_argument('--request-permissions', action='store_true')
    parser.add_argument('--log', type=Path, required=True)
    args = parser.parse_args()
    if not (args.permissions or args.request_permissions):
        parser.error('Use a permission preflight or the separately approved request')
    if args.request_permissions and not json.loads(MANIFEST.read_text()).get('permissionApproved'):
        raise RuntimeError('This exact new app needs approval before its Input Monitoring request')
    process, binary = launch(args.log, ['--request-permissions' if args.request_permissions else '--permissions'])
    try:
        process.wait(timeout=20)
    finally:
        if not stop_launched(process, binary):
            raise RuntimeError('The permission helper did not stop')
        process.wait(timeout=3)
    print(args.log.read_text())

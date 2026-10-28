"""Launch the pinned Veil image or run its separately approved permission request."""

import argparse
import json
from pathlib import Path

from build_veil_browser import APP, MANIFEST, NAME
from launch_pointer_browser import launch as launch_pointer, verified_target as verified_pointer
from process_cleanup import stop_launched


def verified_target():
    return verified_pointer(name=NAME, app_path=APP, manifest_path=MANIFEST)


def launch(log, arguments):
    return launch_pointer(log, arguments, name=NAME, app_path=APP, manifest_path=MANIFEST)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request-permissions', action='store_true')
    parser.add_argument('--log', type=Path, required=True)
    args = parser.parse_args()
    if args.request_permissions and not json.loads(MANIFEST.read_text()).get('permissionApproved'):
        raise RuntimeError('This Veil image needs approval before its Input Monitoring request')
    process, binary = launch(args.log, ['--request-permissions' if args.request_permissions else '--permissions'])
    try:
        process.wait(timeout=20)
    finally:
        if not stop_launched(process, binary):
            raise RuntimeError('Veil permission preflight did not stop')
    print(args.log.read_text())

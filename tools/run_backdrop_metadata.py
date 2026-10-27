"""Inspect owned window metadata and optionally use the frozen guarded capture adapter."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import shutil
import sys
import time

from process_cleanup import matching_pids, stop_owned
from run_native import ROOT, probe
from run_window_capture_reads import run as capture_reads


def run(output, variant, restricted=False, capture=False, use_physical_archive=False):
    output = output.resolve()
    if not output.is_relative_to((ROOT / 'artifacts').resolve()):
        raise ValueError('Use a new project artifact directory')
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    if use_physical_archive and variant != 'compact':
        raise ValueError('The physical archive covers only the compact backdrop')
    binary = ROOT / 'dist/InternalKeyboardControl.app/Contents/MacOS/InternalKeyboardControl'
    if matching_pids(binary):
        raise RuntimeError('An internal diagnostic already runs')
    flags = ['--physical-capture-session'] if variant == 'compact' else ['--backdrop']
    if restricted:
        flags.append('--capture-restricted')
    with (output / 'build.log').open('w') as log:
        subprocess.run(['bash', 'scripts/diagnose-browser-keyboard.sh', *flags, '--build-only'],
                       cwd=ROOT, check=True, timeout=90, stdout=log, stderr=subprocess.STDOUT)
    if use_physical_archive:
        label = 'restricted' if restricted else 'clear'
        recorded = json.loads((ROOT / 'docs/evidence/window-sharing-physical-results.json').read_text())
        expected = next(s['binarySHA256'] for s in recorded['sessions'] if s['name'] == label)
        archive = ROOT / 'artifacts/window-sharing-125' / label / 'tested-image'
        if hashlib.sha256(archive.read_bytes()).hexdigest() != expected or matching_pids(binary):
            raise RuntimeError('Archived image changed or an internal diagnostic started')
        shutil.copy2(archive, binary)
    subprocess.run(['codesign', '--verify', '--strict', str(binary.parents[2])], check=True, timeout=10)
    controller_log = (output / 'controller.log').open('w')
    directory = output / 'session'
    controller = subprocess.Popen([sys.executable, str(ROOT / 'tools/run_window_capture_session.py'),
                                   '--output', str(directory)], cwd=ROOT,
                                  stdout=controller_log, stderr=subprocess.STDOUT)
    session = None
    try:
        deadline = time.monotonic() + 25
        while time.monotonic() < deadline:
            path = directory / 'session.json'
            if path.exists():
                session = json.loads(path.read_text())
                if session.get('pid') and session.get('acceptedInternalSubmissions') and session.get('backdropWindowID'):
                    break
            if controller.poll() is not None:
                raise RuntimeError('Metadata control exited before readiness')
            time.sleep(.1)
        else:
            raise RuntimeError('Metadata control readiness timed out')
        result = subprocess.run([str(ROOT / '.build/OwnedWindowMetadata'), str(session['pid']), session['binarySHA256']],
                                check=True, capture_output=True, text=True, timeout=10)
        metadata = json.loads(result.stdout)
        (output / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
        frozen = probe(['windows', session['pid']], output / 'frozen-windows.json', background=True)
        if capture:
            capture_reads(directory)
        print(json.dumps({'variant': variant, 'restricted': restricted, 'captureAttempted': capture, 'physicalArchiveRestored': use_physical_archive, 'ownedAll': len(metadata['allOwnedWindows']),
                          'ownedOnScreen': len(metadata['onScreenOwnedWindows']),
                          'frozenOnScreen': len(frozen.get('windows', []))}), flush=True)
    finally:
        directory.mkdir(exist_ok=True)
        (directory / 'stop').touch()
        try:
            controller.wait(timeout=15)
        except subprocess.TimeoutExpired:
            if session and hashlib.sha256(binary.read_bytes()).hexdigest() == session['binarySHA256']:
                stop_owned(session.get('pid'), binary)
            controller.terminate()
            controller.wait(timeout=3)
            raise RuntimeError('Research controller cleanup timed out')
        finally:
            controller_log.close()
        final = json.loads((directory / 'session.json').read_text())
        if not final.get('ownedHostStopped') or not final.get('ownedFixtureStopped'):
            raise RuntimeError('Owned research cleanup failed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--variant', choices=['compact', 'full'], required=True)
    parser.add_argument('--restricted', action='store_true')
    parser.add_argument('--capture', action='store_true')
    parser.add_argument('--use-physical-archive', action='store_true')
    args = parser.parse_args()
    run(args.output, args.variant, args.restricted, args.capture, args.use_physical_archive)

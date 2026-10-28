"""Compare scoped filter updates with the exact physically tested window images."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import shutil
import sys
import time

from process_cleanup import matching_pids, stop_owned
from run_capture_refresh_probe import invoke, run as capture
from run_native import ROOT

BINARY = ROOT / 'dist/InternalKeyboardControl.app/Contents/MacOS/InternalKeyboardControl'


def session(output):
    directory = output / 'session'
    log = (output / 'controller.log').open('w')
    controller = subprocess.Popen([sys.executable, str(ROOT / 'tools/run_window_capture_session.py'),
                                   '--window-only', '--output', str(directory)], cwd=ROOT,
                                  stdout=log, stderr=subprocess.STDOUT)
    value = None
    try:
        deadline = time.monotonic() + 25
        while time.monotonic() < deadline:
            path = directory / 'session.json'
            if path.exists():
                value = json.loads(path.read_text())
                if value.get('pid') and value.get('acceptedInternalSubmissions'):
                    break
            if controller.poll() is not None:
                raise RuntimeError('Research control exited before readiness')
            time.sleep(0.1)
        else:
            raise RuntimeError('Research control readiness timed out')
        return capture(output / 'capture', directory / 'session.json')
    finally:
        directory.mkdir(exist_ok=True)
        (directory / 'stop').touch()
        try:
            controller.wait(timeout=15)
        except subprocess.TimeoutExpired:
            if value and hashlib.sha256(BINARY.read_bytes()).hexdigest() == value['binarySHA256']:
                stop_owned(value.get('pid'), BINARY)
            controller.terminate()
            controller.wait(timeout=3)
            raise RuntimeError('Session controller cleanup timed out; stop the comparison')
        finally:
            log.close()
        path = directory / 'session.json'
        final = json.loads(path.read_text()) if path.exists() else {}
        if (not final.get('ownedHostStopped') or not final.get('ownedFixtureStopped')
                or final.get('pid') in matching_pids(BINARY)):
            raise RuntimeError('Owned host or fixture cleanup did not verify')


def score(result):
    recovered = {r['stage'] for r in result.get('recoveries', [])
                 if r['markerRecovery'].get('exact') or r['markerRecovery'].get('visualHexAliases')}
    stages = {'initial-window-filter', 'updated-app-filter', 'updated-window-filter'}
    sampled = {r['stage'] for r in result.get('recoveries', []) if r.get('ocrAvailable')}
    return {'markerRecoveredStages': sorted(recovered),
            'allStagesSampledWithOCR': sampled == stages,
            'allStagesReadable': recovered == stages,
            'streamStopped': result.get('streamStopped') is True}


def run(output):
    output = output.resolve()
    if not output.is_relative_to((ROOT / 'artifacts').resolve()):
        raise ValueError('Use a new directory inside project artifacts')
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    report = {'status': 'inconclusive', 'rows': [], 'systemInputPosted': False}
    try:
        if matching_pids(BINARY):
            raise RuntimeError('An internal research diagnostic already runs')
        permission = invoke(['--permissions'], output / 'permissions.json')
        if not permission.get('screenRecordingGranted'):
            report['status'] = 'permission-required'
            return report
        physical = json.loads((ROOT / 'docs/evidence/window-sharing-physical-results.json').read_text())
        frozen = physical['frozenImagesSHA256']
        for name, expected in frozen.items():
            binary = ROOT / 'dist' / (name + '.app') / 'Contents/MacOS' / name
            if hashlib.sha256(binary.read_bytes()).hexdigest() != expected:
                raise RuntimeError('A frozen permissioned image changed')
        for name, previous in [('clear-before', 'normal-clear'), ('restricted', 'normal-restricted'),
                               ('clear-after', 'normal-clear')]:
            directory = output / name
            directory.mkdir(mode=0o700)
            expected = next(s['binarySHA256'] for s in physical['sessions'] if s['name'] == previous)
            archive = ROOT / 'artifacts/window-sharing-125' / previous / 'tested-image'
            if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
                raise RuntimeError('Archived physical-test image changed')
            if matching_pids(BINARY):
                raise RuntimeError('Refuse to replace a running research diagnostic')
            shutil.copy2(archive, BINARY)
            with (directory / 'signature-check.log').open('w') as log:
                subprocess.run(['codesign', '--verify', '--strict', str(BINARY.parents[2])],
                               stdout=log, stderr=subprocess.STDOUT, check=True, timeout=10)
            if hashlib.sha256(BINARY.read_bytes()).hexdigest() != expected:
                raise RuntimeError('Installed image differs from the physical comparison')
            result = session(directory)
            row = {'name': name, 'binarySHA256': expected, 'originalSignatureVerified': True, **score(result)}
            report['rows'].append(row)
            print(json.dumps(row), flush=True)
            if not row['streamStopped']:
                raise RuntimeError('Stream cleanup is inconclusive')
            if name.startswith('clear') and not row['allStagesReadable']:
                raise RuntimeError('Clear-reference recovery failed')
        trial = next(r for r in report['rows'] if r['name'] == 'restricted')
        report['status'] = ('marker-recovered' if trial['markerRecoveredStages'] else
                            'absent-in-sampled-frames' if trial['allStagesSampledWithOCR'] else
                            'inconclusive-no-candidate-frames')
        report['scope'] = 'Exact physically tested diagnostic images. Sampled owned-window/app filters only. No continuous or unfiltered-display claim.'
        return report
    except Exception as error:
        report['error'] = str(error)
        raise
    finally:
        (output / 'comparison.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    print(json.dumps(run(parser.parse_args().output)), flush=True)

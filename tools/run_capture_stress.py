"""Compare capture-type changes or a longer stream on owned research windows."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from process_cleanup import matching_pids, stop_launched
from run_backdrop_metadata import run as trial
from run_compositor_refresh_comparison import score
from run_native import ROOT, probe
from run_pixel_agent_audit import marker_recovery

MANIFEST = ROOT / 'docs/evidence/capture-stress-permission-manifest.json'
STAGES = {'sequence': ['initial-display', 'independent-window', 'returned-display'],
          'steady': ['steady-display']}


def invoke(arguments, output):
    manifest = json.loads(MANIFEST.read_text())
    app = Path(manifest['path'])
    binary = app / 'Contents/MacOS/CaptureStressProbe'
    source = ROOT / 'Sources/Diagnostics/CaptureStressProbe.swift'
    if (hashlib.sha256(binary.read_bytes()).hexdigest() != manifest['executableSHA256']
            or hashlib.sha256(source.read_bytes()).hexdigest() != manifest['sourceSHA256']):
        raise RuntimeError('The pinned capture helper changed')
    if arguments != ['--permissions'] and not manifest.get('permissionApproved'):
        raise RuntimeError('This helper needs separate consent before capture or a permission request')
    subprocess.run(['codesign', '--verify', '--strict', str(app)], check=True, timeout=10)
    existing = matching_pids(binary)
    if existing:
        raise RuntimeError('The capture stress helper already runs')
    launcher = subprocess.Popen(['open', '-g', '-n', '-W', str(app), '--args', *map(str, arguments),
                                 '--out', str(output)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    launcher.research_existing_pids = existing
    try:
        launcher.wait(timeout=70)
        return json.loads(output.read_text())
    finally:
        clean = stop_launched(launcher, binary)
        if launcher.poll() is None:
            launcher.terminate()
            launcher.wait(timeout=3)
        if not clean:
            raise RuntimeError('The capture stress helper did not stop')


def permission_preflight(output, require_consent=False):
    if require_consent and not json.loads(MANIFEST.read_text()).get('permissionApproved'):
        raise RuntimeError('This helper needs separate Screen Recording consent')
    result = invoke(['--permissions'], output)
    if require_consent and not result.get('screenRecordingGranted'):
        raise RuntimeError('This helper has no effective Screen Recording grant')
    return result


def capture_session(output, session_path, mode):
    if mode not in STAGES:
        raise ValueError('Use sequence or steady capture mode')
    output = output.resolve()
    if not output.is_relative_to((ROOT / 'artifacts').resolve()):
        raise ValueError('Use a new project artifact directory')
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    session = json.loads(session_path.read_text())
    binary = ROOT / 'dist/InternalKeyboardControl.app/Contents/MacOS/InternalKeyboardControl'
    if (session.get('windowOnly') or not session.get('targetWindowID') or not session.get('backdropWindowID')
            or session['pid'] not in matching_pids(binary)
            or hashlib.sha256(binary.read_bytes()).hexdigest() != session['binarySHA256']):
        raise RuntimeError('The exact owned research session is no longer live')
    result = invoke([mode, session['pid'], session['targetWindowID'], session['backdropWindowID'],
                     session['binarySHA256']], output / 'sequence.json')
    recoveries = []
    for stage in result.get('stages', []):
        for name in stage['images']:
            image = Path(name).resolve()
            if not image.is_relative_to(output) or not image.is_file():
                raise RuntimeError('A helper image is outside this run')
            ocr = probe(['ocr', image], image.with_suffix('.ocr.json'), background=True)
            recoveries.append({'stage': stage['stage'], 'image': str(image),
                               'ocrAvailable': isinstance(ocr.get('text'), list),
                               'markerRecovery': marker_recovery(ocr, session['secret']),
                               'backdropLabelRecovered': 'controlled research backdrop' in json.dumps(ocr).lower()})
    summary = {'status': result['status'], 'streamStopped': result.get('streamStopped'),
               'targetPID': session['pid'], 'targetBinarySHA256': session['binarySHA256'],
               'windowSharingEnabled': session['windowSharingEnabled'], 'recoveries': recoveries,
               'stageReports': result.get('stages', [])}
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    return summary


def run(output, mode):
    output = output.resolve()
    if not output.is_relative_to((ROOT / 'artifacts').resolve()):
        raise ValueError('Use a new project artifact directory')
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    report = {'status': 'inconclusive', 'mode': mode, 'rows': [], 'systemInputPosted': False}
    try:
        if not json.loads(MANIFEST.read_text()).get('permissionApproved'):
            report['status'] = 'consent-required'
            return report
        permission_preflight(output / 'permissions.json', require_consent=True)
        frozen = json.loads((ROOT / 'docs/evidence/window-sharing-physical-results.json').read_text())['frozenImagesSHA256']
        for name in ['CaptureRefreshProbe', 'CompositorRefreshProbe']:
            filename = 'capture-refresh' if name == 'CaptureRefreshProbe' else 'compositor-refresh'
            frozen[name] = json.loads((ROOT / f'docs/evidence/{filename}-permission-manifest.json').read_text())['executableSHA256']
        for name, expected in frozen.items():
            binary = ROOT / 'dist' / (name + '.app') / 'Contents/MacOS' / name
            if hashlib.sha256(binary.read_bytes()).hexdigest() != expected:
                raise RuntimeError('An earlier granted image changed')
        for name in ['clear-before', 'restricted', 'clear-after']:
            directory = output / name
            trial(directory, 'compact', restricted=name == 'restricted',
                  use_physical_archive=True, capture_stress=mode)
            row = score(directory, name, subdirectory='capture-stress', stages=STAGES[mode])
            report['rows'].append(row)
            print(json.dumps(row), flush=True)
            if row['streamStopped'] is not True:
                raise RuntimeError('A stream failed before verified shutdown')
            if name.startswith('clear') and (row['error'] or row['status'] != 'sampled' or not row['allStagesReadable']):
                raise RuntimeError('A clear reference failed calibration')
        candidate = next(r for r in report['rows'] if r['name'] == 'restricted')
        if any(s['pageSamples'] for s in candidate['stages']):
            report['status'] = 'page-recovered'
        elif candidate['error'] or candidate['status'] != 'sampled' or not candidate['allStagesSampled']:
            report['status'] = 'inconclusive-no-candidate-samples'
        elif all(s['backdropSamples'] == s['imagesSaved'] for s in candidate['stages']):
            report['status'] = 'backdrop-only-in-sampled-frames'
        else:
            report['status'] = 'page-absent-in-sampled-frames'
        return report
    except Exception as error:
        report['error'] = str(error)
        raise
    finally:
        (output / 'comparison.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--mode', choices=STAGES, default='sequence')
    parser.add_argument('--preflight', action='store_true')
    args = parser.parse_args()
    result = permission_preflight(args.output) if args.preflight else run(args.output, args.mode)
    print(json.dumps(result), flush=True)
